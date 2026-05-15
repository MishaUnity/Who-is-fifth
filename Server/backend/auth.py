import secrets
import logging
from typing import Optional

from fastapi import Request, HTTPException, status

from . import database as db

logger = logging.getLogger(__name__)

_sessions: dict[str, str] = {}


def create_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = user_id
    logger.info("Session created for user_id=%s", user_id)
    return token


def get_session(token: str) -> Optional[str]:
    return _sessions.get(token)


def destroy_session(token: str) -> None:
    _sessions.pop(token, None)


def _extract_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


async def get_current_user(request: Request) -> Optional[str]:
    """Необязательная авторизация — возвращает user_id или None."""
    token = _extract_token(request)
    if token:
        return get_session(token)
    return None


async def require_user(request: Request) -> str:
    """Обязательная авторизация — возвращает user_id или бросает 401."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
    user_id = get_session(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия не найдена или истекла")
    return user_id