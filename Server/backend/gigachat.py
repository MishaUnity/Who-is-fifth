<<<<<<< HEAD
import base64
import os
import time
import json
import logging
import requests
from typing import Generator

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
=======
import os
import time
import logging
import base64
import uuid

import httpx

logger = logging.getLogger(__name__)

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
TOKEN_TTL_SECONDS = 1800  # 30 минут

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Ты — ИИ-помощник корпоративного сервиса компании АИСА. "
    "Помогай пользователям находить информацию: афиша, расписание, "
    "библиотека, каталог, база знаний. "
    "Отвечай кратко, по делу, на русском языке.",
)
>>>>>>> 6c322657c0d254ad8b6b98bd2f5b400b4e770f66


class GigaChatClient:
    def __init__(self):
<<<<<<< HEAD
        self.auth_key = "MDE5ZDJhNTktMzg2YS03ZDM0LThmMTUtMWIyNTM5ZDNjNzA0OjQwYjhmNjFhLWJiM2EtNGU4Ni04MzE1LTJmOWU3MjNhMTZlYQ=="
        self.model = os.getenv("GIGACHAT_MODEL", "GigaChat")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._configured = bool(self.auth_key)

    def _token_is_valid(self):
        return self._access_token is not None and time.time() < (self._token_expires_at - 60)

    def get_token(self) -> str | None:
        if not self._configured:
            return None
        if self._token_is_valid():
            return self._access_token
        try:
            response = requests.post(
                OAUTH_URL,
                headers={
                    "Authorization": f"Basic {self.auth_key}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"scope": "GIGACHAT_API_PERS"},
                timeout=30.0,
                verify=False,
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            expires_at = data.get("expires_at", 0)
            self._token_expires_at = expires_at / 1000.0 if expires_at > 1e12 else time.time() + 1800
            return self._access_token
        except Exception as exc:
            self._access_token = None
            return None

    def chat(self, messages: list[dict], stream: bool = False) -> dict | Generator[str, None, None]:
        if not self._configured:
            msg = "GigaChat не настроен: укажите GIGACHAT_AUTH_KEY."
            return self._error_gen(msg) if stream else {"content": msg, "tokens_used": 0}

        token = self.get_token()
        if token is None:
            msg = "Не удалось получить токен GigaChat. Проверьте GIGACHAT_AUTH_KEY."
            return self._error_gen(msg) if stream else {"content": msg, "tokens_used": 0}

        payload = {"model": self.model, "messages": messages, "stream": stream}

        if stream:
            return self._stream_chat(token, payload)

        try:
            response = requests.post(
                CHAT_URL,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=60.0,
                verify=False,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
            }
        except requests.HTTPError as exc:
            return {"content": f"Ошибка GigaChat (HTTP {exc.response.status_code}).", "tokens_used": 0}
        except Exception as exc:
            return {"content": "Произошла ошибка при обращении к GigaChat.", "tokens_used": 0}

    def _stream_chat(self, token: str, payload: dict) -> Generator[str, None, None]:
        try:
            with requests.post(
                CHAT_URL,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
                timeout=120.0,
                verify=False,
                stream=True,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode("utf-8") if isinstance(line, bytes) else line
                    if not decoded.startswith("data: "):
                        continue
                    data_str = decoded[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)["choices"][0].get("delta", {}).get("content", "")
                        if chunk:
                            yield chunk
                    except Exception:
                        continue
        except Exception as exc:
            yield "Ошибка при получении потокового ответа от GigaChat."

    @staticmethod
    def _error_gen(message: str) -> Generator[str, None, None]:
        yield message
=======
        self.client_id = os.getenv("GIGACHAT_CLIENT_ID", "")
        self.client_secret = os.getenv("GIGACHAT_CLIENT_SECRET", "")
        self.model = os.getenv("GIGACHAT_MODEL", "GigaChat")
        self.mock = os.getenv("GIGACHAT_MOCK", "false").lower() == "true"
        self.access_token = None
        self.token_expires_at = 0

        if not self.is_configured() and not self.mock:
            logger.warning(
                "GigaChat credentials not set. "
                "Set GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET, "
                "or enable GIGACHAT_MOCK=true for development."
            )

    def is_configured(self):
        return bool(self.client_id and self.client_secret)

    def token_is_valid(self):
        return self.access_token is not None and time.time() < self.token_expires_at - 60

    async def get_token(self):
        if not self.is_configured():
            return None

        if self.token_is_valid():
            return self.access_token

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    OAUTH_URL,
                    headers={
                        "Authorization": f"Basic {encoded}",
                        "RqUID": str(uuid.uuid4()),  # уникальный ID каждого запроса
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={"scope": os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

                self.access_token = data["access_token"]
                expires_at = data.get("expires_at", 0)
                if expires_at > 1e12:
                    self.token_expires_at = expires_at / 1000.0
                else:
                    self.token_expires_at = time.time() + TOKEN_TTL_SECONDS

                logger.info("GigaChat token refreshed")
                return self.access_token

        except Exception as e:
            logger.error("Failed to get GigaChat token: %s", e)
            self.access_token = None
            return None

    async def chat(self, history: list, user_message: str) -> dict:
        """
        Отправляет историю + новый вопрос в GigaChat.

        Аргументы:
            history      — предыдущие сообщения из БД:
                           [{"role": "user"|"assistant", "content": "..."}]
            user_message — текущий вопрос пользователя

        Возвращает {"content": str, "tokens_used": int}
        """
        if self.mock:
            return {"content": self._mock(user_message), "tokens_used": 0}

        if not self.is_configured():
            return {
                "content": "GigaChat не настроен: укажите GIGACHAT_CLIENT_ID и GIGACHAT_CLIENT_SECRET.",
                "tokens_used": 0,
            }

        token = await self.get_token()
        if token is None:
            return {
                "content": "Не удалось получить токен доступа GigaChat. Проверьте учётные данные.",
                "tokens_used": 0,
            }

        # Системный промпт + история + новый вопрос
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    CHAT_URL,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1024,
                    },
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                return {"content": content, "tokens_used": tokens_used}

        except httpx.HTTPStatusError as e:
            logger.error("GigaChat HTTP error %s: %s", e.response.status_code, e.response.text)
            return {
                "content": f"Ошибка GigaChat (HTTP {e.response.status_code}). Попробуйте позже.",
                "tokens_used": 0,
            }
        except Exception as e:
            logger.error("GigaChat request failed: %s", e)
            return {
                "content": "Произошла ошибка при обращении к GigaChat. Попробуйте позже.",
                "tokens_used": 0,
            }

    def _mock(self, message: str) -> str:
        """Заглушка для разработки без реального GigaChat."""
        msg = message.lower()

        if any(w in msg for w in ["привет", "здравств", "hello"]):
            return "Привет! Я ИИ-помощник сервиса АИСА. Чем могу помочь?"

        if any(w in msg for w in ["афиш", "мероприят", "событи", "концерт"]):
            return (
                "В ближайшие дни запланированы:\n"
                "• 17 мая — лекция «Цифровая трансформация», 14:00, зал А\n"
                "• 20 мая — мастер-класс по управлению проектами, 10:00\n\n"
                "Уточните интересующую дату?"
            )

        if any(w in msg for w in ["расписани", "когда", "время"]):
            return "Расписание доступно в разделе «Афиша». Укажите дату или мероприятие — уточню."

        if any(w in msg for w in ["библиотек", "книг", "материал"]):
            return (
                "В библиотеке доступно более 500 материалов. "
                "Что вас интересует: книги, обучающие курсы или статьи?"
            )

        if any(w in msg for w in ["помог", "умеешь", "можешь"]):
            return (
                "Я могу помочь вам:\n"
                "• Найти мероприятие в афише\n"
                "• Узнать расписание\n"
                "• Найти материал в библиотеке\n"
                "• Ответить на уточняющие вопросы\n\n"
                "Задайте свой вопрос!"
            )

        return (
            f"Вы спросили: «{message}»\n\n"
            "Это демо-режим (GIGACHAT_MOCK=true). "
            "Укажите GIGACHAT_CLIENT_ID и GIGACHAT_CLIENT_SECRET в .env для боевого режима."
        )


# Синглтон — один клиент на всё приложение
gigachat = GigaChatClient()
>>>>>>> 6c322657c0d254ad8b6b98bd2f5b400b4e770f66
