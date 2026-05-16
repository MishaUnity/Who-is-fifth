import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

import aiosqlite
import bcrypt

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "aisa.db")


async def _get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_pool() -> None:
    """Создаём таблицы при старте если их нет."""
    db = await _get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS token_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT,
                tokens_used INTEGER NOT NULL DEFAULT 0,
                endpoint TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Создаём админа если его нет
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, password_hash, role, is_admin)
            VALUES (
                '00000000-0000-0000-0000-000000000001',
                'admin',
                '$2b$12$KIXuCaUkJUHFmJFpFzBgqeJFtYFDMUXDmJjuiLzDHhDwBdK5vkMom',
                'admin',
                1
            )
        """)
        await db.commit()
        logger.info("Database initialised at %s", DB_PATH)
    finally:
        await db.close()


async def close_pool() -> None:
    """Для совместимости с main.py — SQLite не требует закрытия пула."""
    logger.info("Database closed")


# ── Users ─────────────────────────────────────────────────────────────

async def create_user(
    username: str,
    password: str,
    role: str = "user",
    is_admin: bool = False,
) -> str:
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = datetime.now(timezone.utc).isoformat()

    db = await _get_db()
    try:
        await db.execute(
            """
            INSERT INTO users (id, username, password_hash, role, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, password_hash, role, int(is_admin), now)
        )
        await db.commit()
    finally:
        await db.close()
    return user_id


async def verify_user(username: str, password: str) -> Optional[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT id, username, password_hash, role, is_admin FROM users WHERE username = ?",
            (username,)
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    if row is None:
        return None
    if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return {
            "id":       row["id"],
            "username": row["username"],
            "role":     row["role"],
            "is_admin": bool(row["is_admin"]),
        }
    return None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT id, username, role, is_admin, is_active, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    if row is None:
        return None
    return {
        "id":         row["id"],
        "username":   row["username"],
        "role":       row["role"],
        "is_admin":   bool(row["is_admin"]),
        "is_active":  bool(row["is_active"]),
        "created_at": row["created_at"],
    }


async def get_all_users() -> list[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute("""
            SELECT
                u.id, u.username, u.role, u.is_admin, u.is_active, u.created_at,
                COUNT(DISTINCT s.id)  AS total_sessions,
                COUNT(m.id)           AS total_messages
            FROM users u
            LEFT JOIN sessions s ON s.user_id = u.id
            LEFT JOIN messages m ON m.session_id = s.id AND m.role = 'user'
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        rows = await cursor.fetchall()
    finally:
        await db.close()

    return [{
        "id":             r["id"],
        "username":       r["username"],
        "role":           r["role"],
        "is_admin":       bool(r["is_admin"]),
        "is_active":      bool(r["is_active"]),
        "created_at":     r["created_at"],
        "total_sessions": r["total_sessions"],
        "total_messages": r["total_messages"],
    } for r in rows]


# ── Sessions ──────────────────────────────────────────────────────────

async def ensure_session(session_id: str, user_id: Optional[str] = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db = await _get_db()
    try:
        await db.execute("""
            INSERT INTO sessions (id, user_id, created_at, last_active)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET last_active = excluded.last_active
        """, (session_id, user_id, now, now))
        await db.commit()
    finally:
        await db.close()


async def get_user_sessions(user_id: str) -> list[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute("""
            SELECT id, created_at, last_active
            FROM sessions WHERE user_id = ?
            ORDER BY last_active DESC
        """, (user_id,))
        rows = await cursor.fetchall()
    finally:
        await db.close()
    return [dict(r) for r in rows]


async def delete_session(session_id: str, user_id: str) -> bool:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "DELETE FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0
    finally:
        await db.close()


# ── Messages ──────────────────────────────────────────────────────────

async def save_message(session_id: str, role: str, content: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db = await _get_db()
    try:
        await db.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now)
        )
        await db.execute(
            "UPDATE sessions SET last_active = ? WHERE id = ?",
            (now, session_id)
        )
        await db.commit()
    finally:
        await db.close()


async def get_history(session_id: str) -> list[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


# ── Token log ─────────────────────────────────────────────────────────

async def log_tokens(
    session_id: str,
    user_id: Optional[str],
    tokens: int,
    endpoint: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    db = await _get_db()
    try:
        await db.execute(
            "INSERT INTO token_log (session_id, user_id, tokens_used, endpoint, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, tokens, endpoint, now)
        )
        await db.commit()
    finally:
        await db.close()


async def get_stats() -> dict:
    db = await _get_db()
    try:
        cursor = await db.execute("""
            SELECT
                COUNT(DISTINCT u.id)                                    AS total_users,
                COUNT(DISTINCT s.id)                                    AS total_sessions,
                COUNT(CASE WHEN m.role = 'user' THEN 1 END)            AS total_requests,
                COUNT(CASE WHEN m.role = 'user'
                    AND date(m.created_at) = date('now') THEN 1 END)   AS requests_today,
                COUNT(DISTINCT CASE WHEN date(s.last_active) = date('now')
                    THEN s.id END)                                      AS sessions_today,
                COALESCE(SUM(tl.tokens_used), 0)                       AS total_tokens,
                COALESCE(SUM(CASE WHEN date(tl.created_at) = date('now')
                    THEN tl.tokens_used END), 0)                        AS tokens_today
            FROM users u
            LEFT JOIN sessions  s  ON s.user_id    = u.id
            LEFT JOIN messages  m  ON m.session_id = s.id
            LEFT JOIN token_log tl ON tl.user_id   = u.id
        """)
        totals = await cursor.fetchone()

        cursor = await db.execute("""
            SELECT
                date(m.created_at)           AS day,
                COUNT(*)                     AS requests,
                COALESCE(SUM(tl.tokens_used), 0) AS tokens
            FROM messages m
            LEFT JOIN token_log tl
                ON tl.session_id = m.session_id
                AND date(tl.created_at) = date(m.created_at)
            WHERE m.role = 'user'
              AND m.created_at >= date('now', '-6 days')
            GROUP BY day ORDER BY day ASC
        """)
        daily = await cursor.fetchall()

        cursor = await db.execute("""
            SELECT
                u.username,
                COUNT(m.id)                      AS requests,
                COALESCE(SUM(tl.tokens_used), 0) AS tokens
            FROM users u
            JOIN sessions  s  ON s.user_id    = u.id
            JOIN messages  m  ON m.session_id = s.id AND m.role = 'user'
            LEFT JOIN token_log tl ON tl.user_id = u.id
            WHERE u.is_admin = 0
            GROUP BY u.id
            ORDER BY requests DESC
            LIMIT 5
        """)
        top_users = await cursor.fetchall()

    finally:
        await db.close()

    return {
        "total_users":    totals["total_users"],
        "total_sessions": totals["total_sessions"],
        "total_requests": totals["total_requests"],
        "requests_today": totals["requests_today"],
        "sessions_today": totals["sessions_today"],
        "total_tokens":   totals["total_tokens"],
        "tokens_today":   totals["tokens_today"],
        "daily_activity": [dict(r) for r in daily],
        "top_users":      [dict(r) for r in top_users],
    }