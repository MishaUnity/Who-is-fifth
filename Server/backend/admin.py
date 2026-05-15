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
async def admin_stats(current_user: dict = Depends(require_admin)):
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