from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_stats, get_all_users, get_user_by_id
from app.auth import require_admin   # dependency — см. ниже

router = APIRouter(prefix="/admin", tags=["Администратор"])


# ── Схемы ответов ─────────────────────────────────────────────────────

class DailyActivity(BaseModel):
    day: datetime
    requests: int
    tokens: int

class TopUser(BaseModel):
    username: str
    requests: int
    tokens: int

class StatsResponse(BaseModel):
    # Всего за всё время
    total_users:    int
    total_sessions: int
    total_requests: int
    total_tokens:   int
    # За сегодня
    requests_today: int
    sessions_today: int
    tokens_today:   int
    # Детализация
    daily_activity: list[DailyActivity]
    top_users:      list[TopUser]

class AdminUserResponse(BaseModel):
    id:               str
    username:         str
    role:             str
    is_admin:         bool
    created_at:       datetime
    total_sessions:   int
    total_messages:   int


# ── Эндпоинты ─────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
async def admin_stats(request: Request, current_user: dict = Depends(require_admin)):
    """
    Статистика для окна администратора.
    Требует: is_admin = true.
    """
    return await get_stats()


@router.get("/users", response_model=list[AdminUserResponse])
async def admin_users(current_user: dict = Depends(require_admin)):
    """
    Все пользователи с агрегатами активности.
    Требует: is_admin = true.
    """
    return await get_all_users()


@router.patch("/users/{user_id}/toggle-admin", response_model=AdminUserResponse)
async def toggle_admin(
    user_id: str,
    current_user: dict = Depends(require_admin),
):
    """Выдать / забрать права администратора."""
    if user_id == current_user["id"]:
        raise HTTPException(400, "Нельзя изменить права самому себе")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(404, "Пользователь не найден")

    # TODO: обновить is_admin в БД
    return {**user, "is_admin": not user["is_admin"]}

class TokenStatsResponse(BaseModel):
    period: str          # "2026-05-15"
    requests: int
    tokens_used: int
    sessions_opened: int

class DetailedStatsResponse(BaseModel):
    # Суммарно
    total_users: int
    total_sessions: int
    total_requests: int
    total_tokens: int
    avg_tokens_per_request: float
    avg_messages_per_session: float
    # Сегодня
    requests_today: int
    tokens_today: int
    sessions_today: int
    # По дням (для графика)
    daily: list[TokenStatsResponse]
    # Топ
    top_users: list[TopUser]


@router.get("/detailed-stats", response_model=DetailedStatsResponse)
async def detailed_stats(
    days: int = 7,
    current_user: dict = Depends(require_admin),
):
    """
    Расширенная статистика для отдельного окна администратора.

    Параметры:
        days — за сколько дней показывать график (7, 14, 30)

    Требует: is_admin = true
    """
    # TODO: реальный запрос к БД будет выглядеть так:
    # async with get_pool().acquire() as conn:
    #     daily = await conn.fetch("""
    #         SELECT
    #             created_at::date          AS period,
    #             COUNT(*)                  AS requests,
    #             COALESCE(SUM(tl.tokens_used), 0) AS tokens_used,
    #             COUNT(DISTINCT m.session_id)      AS sessions_opened
    #         FROM messages m
    #         LEFT JOIN token_log tl ON tl.session_id = m.session_id
    #             AND tl.created_at::date = m.created_at::date
    #         WHERE m.role = 'user'
    #           AND m.created_at >= CURRENT_DATE - ($1 - 1) * INTERVAL '1 day'
    #         GROUP BY period
    #         ORDER BY period ASC
    #     """, days)

    return {
        "total_users": 42,
        "total_sessions": 156,
        "total_requests": 890,
        "total_tokens": 124500,
        "avg_tokens_per_request": 139.9,
        "avg_messages_per_session": 5.7,
        "requests_today": 47,
        "tokens_today": 6300,
        "sessions_today": 12,
        "daily": [
            {"period": "2026-05-10", "requests": 95,  "tokens_used": 13200, "sessions_opened": 18},
            {"period": "2026-05-11", "requests": 112, "tokens_used": 15800, "sessions_opened": 22},
            {"period": "2026-05-12", "requests": 78,  "tokens_used": 10900, "sessions_opened": 15},
            {"period": "2026-05-13", "requests": 134, "tokens_used": 18700, "sessions_opened": 26},
            {"period": "2026-05-14", "requests": 156, "tokens_used": 21800, "sessions_opened": 30},
            {"period": "2026-05-15", "requests": 168, "tokens_used": 23500, "sessions_opened": 33},
            {"period": "2026-05-16", "requests": 47,  "tokens_used": 6300,  "sessions_opened": 12},
        ],
        "top_users": [
            {"username": "ivanov",  "requests": 312, "tokens": 44100},
            {"username": "petrova", "requests": 198, "tokens": 27800},
            {"username": "sidorov", "requests": 132, "tokens": 18500},
            {"username": "kozlov",  "requests": 88,  "tokens": 12300},
            {"username": "morozov", "requests": 54,  "tokens": 7600},
        ],
    }