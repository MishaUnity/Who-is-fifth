from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from database import create_user, verify_user
from auth import create_session, destroy_session, require_user

router = APIRouter(prefix="/auth", tags=["Авторизация"])


class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    is_admin: bool


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest):
    try:
        user_id = await create_user(data.username, data.password)
    except Exception:
        raise HTTPException(status_code=400, detail="Username уже занят")
    return {"id": user_id, "username": data.username, "role": "user", "is_admin": False}


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    user = await verify_user(data.username, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    token = create_session(user["id"])
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(request: Request):
    from app.auth import _extract_token, destroy_session
    token = _extract_token(request)
    if token:
        destroy_session(token)
    return {"detail": "Вышли из системы"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(require_user)):
    return current_user