import base64
import os
import time
import json
import logging
import requests
from typing import Generator

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


class GigaChatClient:
    def __init__(self):
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
