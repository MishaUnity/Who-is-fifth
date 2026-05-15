import os
import logging
import asyncio

from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .gigachat import GigaChatClient
from . import afisha as afisha_client
from . import database as db
from .auth import create_session, destroy_session, get_current_user, require_user
<<<<<<< HEAD
from app.database import init_pool, close_pool
=======

from contextlib import asynccontextmanager
from .database import init_pool, close_pool
>>>>>>> 46607b5ee144af0a1227f35e471cd2bb5441c619

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    await init_pool()
    logger.info("App started")
    yield
    await close_pool()


app = FastAPI(title="Афиша-СИРИУС ИИ-Ассистент", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

gigachat = GigaChatClient()

SYSTEM_PROMPT = (
    "Ты — ИИ-ассистент сервиса Афиша-СИРИУС. "
    "Помогай пользователям находить мероприятия и отвечай на вопросы. "
    "Используй предоставленные данные о мероприятиях."
    ""
)


class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: list = []

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Auth ───────────────────────────────────────────────────────────────

@app.post("/api/auth/register", status_code=201)
async def register(payload: RegisterRequest):
    if not payload.username.strip() or not payload.password.strip():
        raise HTTPException(status_code=400, detail="username и password обязательны")
    try:
        user_id = await db.create_user(payload.username.strip(), payload.password)
    except Exception:
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
    token = create_session(user_id)
    return {"token": token, "user_id": user_id}


@app.post("/api/auth/login")
async def login(payload: LoginRequest):
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="username и password обязательны")
    user = await db.verify_user(payload.username.strip(), payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    token = create_session(user["id"])
    return {"token": token, "user_id": user["id"]}


@app.post("/api/auth/logout")
async def logout(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        destroy_session(token)
    return {"message": "Выход выполнен успешно"}


@app.get("/api/auth/me")
async def me(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Не авторизован")
    return {"user_id": current_user}


# ── Chat ───────────────────────────────────────────────────────────────

@app.get("/api/chat/sessions")
async def get_sessions(current_user: str = Depends(require_user)):
    sessions = await db.get_user_sessions(current_user)
    return {"sessions": sessions}


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest, current_user: str = Depends(require_user)):
    message = payload.message.strip()
    session_id = payload.session_id.strip()

    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    await db.ensure_session(session_id, current_user)

    try:
        payload_afisha = await asyncio.get_event_loop().run_in_executor(
            None, lambda: afisha_client.get_events(search=message)
        )
        afisha_context = afisha_client.format_events_for_llm(payload_afisha)
    except Exception as e:
        logger.warning("Afisha error: %s", e)
        afisha_context = ""

    history = await db.get_history(session_id)
    if not history:
        history = payload.history

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + afisha_context}]
    messages.extend(history[-20:])
    messages.append({"role": "user", "content": message})

    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: gigachat.chat(messages)
    )

    await db.save_message(session_id, "user", message)
    await db.save_message(session_id, "assistant", result["content"])
    await db.log_tokens(session_id, current_user, result["tokens_used"], "/api/chat")

    return {
        "content": result["content"],
        "tokens_used": result["tokens_used"],
        "session_id": session_id,
    }


# ── Admin ──────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def get_stats(limit: int = 100, current_user: str = Depends(require_user)):
    entries = await db.get_stats(limit=min(limit, 500))
    total_tokens = sum(e.get("tokens_used", 0) for e in entries)
    return {"total_tokens": total_tokens, "entries": entries, "count": len(entries)}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url, exc)
    return JSONResponse(status_code=500, content={"error": str(exc)})