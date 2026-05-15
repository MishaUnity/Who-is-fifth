import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

import aiosqlite
import bcrypt

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "/app/data/app.db")


async def _get_db() -> aiosqlite.Connection:
    import os as _os
    _os.makedirs(_os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    db = await _get_db()
    try:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
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
            """
        )
        await db.commit()
        logger.info("Database initialised at %s", DB_PATH)
    finally:
        await db.close()


async def save_message(session_id: str, role: str, content: str) -> None:
    db = await _get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        await db.execute(
            "UPDATE sessions SET last_active = ? WHERE id = ?",
            (now, session_id),
        )
        await db.commit()
    finally:
        await db.close()


async def ensure_session(session_id: str, user_id: Optional[str] = None) -> None:
    db = await _get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """
            INSERT INTO sessions (id, user_id, created_at, last_active)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET last_active = excluded.last_active
            """,
            (session_id, user_id, now, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_history(session_id: str) -> list[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]
    finally:
        await db.close()


async def log_tokens(
    session_id: str,
    user_id: Optional[str],
    tokens: int,
    endpoint: str,
) -> None:
    db = await _get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO token_log (session_id, user_id, tokens_used, endpoint, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, user_id, tokens, endpoint, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_stats(limit: int = 100) -> list[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            """
            SELECT id, session_id, user_id, tokens_used, endpoint, created_at
            FROM token_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def create_user(username: str, password: str) -> str:
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db = await _get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, username, password_hash, now),
        )
        await db.commit()
        return user_id
    finally:
        await db.close()


async def verify_user(username: str, password: str) -> Optional[str]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            return row["id"]
        return None
    finally:
        await db.close()
        
async def get_user_sessions(user_id: str) -> list[dict]:
    db = await _get_db()
    try:
        cursor = await db.execute(
            """
            SELECT id, created_at, last_active
            FROM sessions
            WHERE user_id = ?
            ORDER BY last_active DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()