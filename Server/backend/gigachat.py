import uuid
import os
import time
import threading
import logging
import requests

logger = logging.getLogger(__name__)

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL  = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "Ты — ИИ-ассистент сервиса Афиша-СИРИУС федеральной территории «Сириус». "
    "Твоя задача — помогать пользователям находить интересные мероприятия и отвечать на вопросы о них. "
    "Отвечай кратко, дружелюбно и по делу. "
    "Если пользователь спрашивает о мероприятиях — используй только предоставленные данные афиши. "
    "Если подходящих мероприятий нет — честно скажи об этом. "
    "Всегда указывай название, дату, время и место мероприятия."
)


class GigaChatClient:
    def __init__(self):
        self.auth_key    = os.getenv("GIGACHAT_AUTH_ID")
        self.model       = os.getenv("GIGACHAT_MODEL", "GigaChat")
        self._configured = bool(self.auth_key)

        self._access_token: str | None = None
        self._token_expires_at: float  = 0.0
        self._lock = threading.Lock()

        if self._configured:
            self._start_token_rotation()

    def _token_is_valid(self) -> bool:
        return (
            self._access_token is not None
            and time.time() < self._token_expires_at - 60
        )

    def _fetch_token(self) -> bool:
        try:
            response = requests.post(
                OAUTH_URL,
                headers={
                    "Authorization": f"Basic {self.auth_key}",
                    "Content-Type":  "application/x-www-form-urlencoded",
                    "RqUID":         str(uuid.uuid4()),
                },
                data={"scope": "GIGACHAT_API_PERS"},
                timeout=30.0,
                verify=False,
            )
            response.raise_for_status()
            data = response.json()

            with self._lock:
                self._access_token = data["access_token"]
                expires_at = data.get("expires_at", 0)
                self._token_expires_at = (
                    expires_at / 1000.0 if expires_at > 1e12
                    else time.time() + 1800
                )

            logger.info("GigaChat token refreshed, valid until %.0f", self._token_expires_at)
            return True

        except Exception as exc:
            logger.error("Failed to fetch GigaChat token: %s", exc)
            return False

    def _start_token_rotation(self) -> None:
        def _rotation_loop():
            self._fetch_token()
            while True:
                with self._lock:
                    expires_at = self._token_expires_at
                sleep_for = max(expires_at - time.time() - 120, 30)
                logger.debug("Token rotation: sleeping %.0fs", sleep_for)
                time.sleep(sleep_for)
                self._fetch_token()

        thread = threading.Thread(
            target=_rotation_loop,
            daemon=True,
            name="gigachat-token-rotation"
        )
        thread.start()
        logger.info("GigaChat token rotation thread started")

    def get_token(self) -> str | None:
        if not self._configured:
            return None
        with self._lock:
            if self._token_is_valid():
                return self._access_token
        self._fetch_token()
        with self._lock:
            return self._access_token

    def build_messages(
        self,
        user_message: str,
        events_context: str = "",
        history: list[dict] | None = None,
    ) -> list[dict]:
        system_content = SYSTEM_PROMPT
        if events_context:
            system_content += f"\n\nАктуальные мероприятия:\n{events_context}"

        messages = [{"role": "system", "content": system_content}]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": user_message})
        return messages

    def chat(self, messages: list[dict]) -> dict:
        token = self.get_token()
        if not token:
            return {"content": "Не удалось получить токен GigaChat.", "tokens_used": 0}

        try:
            response = requests.post(
                CHAT_URL,
                json={"model": self.model, "messages": messages},
                headers={"Authorization": f"Bearer {token}"},
                timeout=60.0,
                verify=False,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content":     data["choices"][0]["message"]["content"],
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
            }
        except requests.HTTPError as exc:
            logger.error("GigaChat HTTP error: %s", exc.response.status_code)
            return {"content": f"Ошибка GigaChat (HTTP {exc.response.status_code}).", "tokens_used": 0}
        except Exception as exc:
            logger.error("GigaChat request failed: %s", exc)
            return {"content": "Произошла ошибка при обращении к GigaChat.", "tokens_used": 0}
