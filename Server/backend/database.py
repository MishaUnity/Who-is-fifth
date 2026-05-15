import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

import asyncpg
import bcrypt

logger = logging.getLogger(__name__)

# Два варианта конфига — либо полный DSN, либо отдельные переменные
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://{user}:{password}@{host}:{port}/{db}".format(
        user=os.getenv("POSTGRES_USER", "aisa"),
        password=os.getenv("POSTGRES_PASSWORD", "aisa"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        db=os.getenv("POSTGRES_DB", "aisa"),
    ),
)

# Пул соединений — создаётся один раз при старте приложения
_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    """Вызывается один раз в lifespan FastAPI."""
    global _pool
    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=10,
    )
    logger.info("PostgreSQL connection pool created")


async def close_pool() -> None:
    """Вызывается при завершении приложения."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("PostgreSQL connection pool closed")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Pool is not initialised. Call init_pool() first.")
    return _pool


# ── Users ─────────────────────────────────────────────────────────────

async def create_user(username: str, password: str, role: str = "user") -> str:
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = datetime.now(timezone.utc)

    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (id, username, password_hash, role, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            user_id, username, password_hash, role, now,
        )
    return user_id


async def verify_user(username: str, password: str) -> Optional[dict]:
    """Возвращает {"id", "username", "role"} или None."""
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, password_hash, role FROM users WHERE username = $1",
            username,
        )
    if row is None:
        return None
    if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return {"id": row["id"], "username": row["username"], "role": row["role"]}
    return None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, role, created_at FROM users WHERE id = $1",
            user_id,
        )
    return dict(row) if row else None


async def get_all_users() -> list[dict]:
    """Для админки — все пользователи с агрегатами активности."""
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                u.id,
                u.username,
                u.role,
                u.created_at,
                COUNT(DISTINCT s.id)  AS total_sessions,
                COUNT(m.id)           AS total_messages
            FROM users u
            LEFT JOIN sessions s ON s.user_id = u.id
            LEFT JOIN messages m ON m.session_id = s.id AND m.role = 'user'
            GROUP BY u.id
            ORDER BY u.created_at DESC
            """,
        )
    return [dict(r) for r in rows]


# ── Sessions ──────────────────────────────────────────────────────────

async def ensure_session(session_id: str, user_id: Optional[str] = None) -> None:
    now = datetime.now(timezone.utc)
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO sessions (id, user_id, created_at, last_active)
            VALUES ($1, $2, $3, $3)
            ON CONFLICT (id) DO UPDATE SET last_active = excluded.last_active
            """,
            session_id, user_id, now,
        )


async def get_user_sessions(user_id: str) -> list[dict]:
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, created_at, last_active
            FROM sessions
            WHERE user_id = $1
            ORDER BY last_active DESC
            """,
            user_id,
        )
    return [dict(r) for r in rows]


async def delete_session(session_id: str, user_id: str) -> bool:
    """Удаляет сессию и все её сообщения. Возвращает False если не найдена."""
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            result = await conn.execute(
                "DELETE FROM sessions WHERE id = $1 AND user_id = $2",
                session_id, user_id,
            )
    return result != "DELETE 0"


# ── Messages ──────────────────────────────────────────────────────────

async def save_message(session_id: str, role: str, content: str) -> None:
    now = datetime.now(timezone.utc)
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO messages (session_id, role, content, created_at)
                VALUES ($1, $2, $3, $4)
                """,
                session_id, role, content, now,
            )
            await conn.execute(
                "UPDATE sessions SET last_active = $1 WHERE id = $2",
                now, session_id,
            )


async def get_history(session_id: str) -> list[dict]:
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content FROM messages
            WHERE session_id = $1
            ORDER BY id ASC
            """,
            session_id,
        )
    return [{"role": r["role"], "content": r["content"]} for r in rows]


# ── Token log ─────────────────────────────────────────────────────────

async def log_tokens(
    session_id: str,
    user_id: Optional[str],
    tokens: int,
    endpoint: str,
) -> None:
    now = datetime.now(timezone.utc)
    async with get_pool().acquire() as conn:
        await conn.execute(
            """
            INSERT INTO token_log (session_id, user_id, tokens_used, endpoint, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            session_id, user_id, tokens, endpoint, now,
        )


async def get_stats() -> dict:
    """Агрегированная статистика для админки."""
    async with get_pool().acquire() as conn:
        totals = await conn.fetchrow(
            """
            SELECT
                COUNT(DISTINCT u.id)                            AS total_users,
                COUNT(DISTINCT s.id)                            AS total_sessions,
                COUNT(m.id)                                     AS total_messages,
                COUNT(m.id) FILTER (
                    WHERE m.created_at::date = CURRENT_DATE
                )                                               AS messages_today,
                COALESCE(SUM(tl.tokens_used), 0)               AS total_tokens
            FROM users u
            LEFT JOIN sessions s  ON s.user_id  = u.id
            LEFT JOIN messages m  ON m.session_id = s.id AND m.role = 'user'
            LEFT JOIN token_log tl ON tl.user_id = u.id
            """,
        )
        top = await conn.fetch(
            """
            SELECT u.username, COUNT(m.id) AS messages
            FROM users u
            JOIN sessions s  ON s.user_id   = u.id
            JOIN messages m  ON m.session_id = s.id AND m.role = 'user'
            GROUP BY u.id
            ORDER BY messages DESC
            LIMIT 5
            """,
        )
    return {
        **dict(totals),
        "top_users": [dict(r) for r in top],
    }