from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

from gigachat import GigaChatClient
from afisha import get_events, format_events_for_llm
from datetime import datetime, timedelta, timezone

gigachat = GigaChatClient()

# 1. Проверка токена
print("Токен получен:", gigachat.get_token() is not None)

# 2. Простой вопрос без афиши
messages = gigachat.build_messages("Привет! Ты кто?")
result = gigachat.chat(messages)
print("\n[Без афиши]")
print("Ответ:", result["content"])
print("Токенов:", result["tokens_used"])

# 3. Вопрос с контекстом афиши
begin = datetime.now(timezone.utc)
end = begin + timedelta(days=30)
payload = get_events(
    begin_date=begin.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    end_date=end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    limit=20
)
events_context = format_events_for_llm(payload)

messages = gigachat.build_messages(
    user_message="Что интересного можно посетить на этой неделе?",
    events_context=events_context,
)
result = gigachat.chat(messages)
print("\n[С афишей]")
print("Ответ:", result["content"])
print("Токенов:", result["tokens_used"])
