import secrets
import logging
from typing import Optional

from fastapi import Request, HTTPException, status, Depends

from database import get_user_by_id

logger = logging.getLogger(__name__)

# Сессии хранятся в памяти: token → user_id
# При рестарте сервера все сессии сбрасываются
_sessions: dict[str, str] = {}


def create_session(user_id: str) -> str:
    """Создаёт токен сессии и привязывает его к user_id."""
    token = secrets.token_urlsafe(32)
    _sessions[token] = user_id
    logger.info("Session created for user_id=%s", user_id)
    return token


def get_session(token: str) -> Optional[str]:
    """Возвращает user_id по токену или None."""
    return _sessions.get(token)


def destroy_session(token: str) -> None:
    """Удаляет сессию (logout)."""
    _sessions.pop(token, None)


def _extract_token(request: Request) -> Optional[str]:
    """Достаёт Bearer токен из заголовка Authorization."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Необязательная авторизация.
    Возвращает dict пользователя из БД или None.
    """
    token = _extract_token(request)
    if not token:
        return None
    user_id = get_session(token)
    if not user_id:
        return None
    return await get_user_by_id(user_id)


async def require_user(request: Request) -> dict:
    """
    Обязательная авторизация.
    Возвращает dict пользователя или бросает 401.
    """
    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация"
        )
    user_id = get_session(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия не найдена или истекла"
        )
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    return user


async def require_admin(request: Request) -> dict:
    """
    Только для администраторов.
    Возвращает dict пользователя или бросает 403.
    """
    user = await require_user(request)
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для администраторов"
        )
    return user