from gigachat import GigaChatClient

from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).parent.parent / ".env")

from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
print("Путь к .env:", env_path)
print("Файл существует:", env_path.exists())

# Выведем все переменные окружения связанные с GIGA
for key, value in os.environ.items():
    if "GIGA" in key:
        print(f"{key} = {value[:10]}...")  # первые 10 символов для безопасности

client = GigaChatClient()

# Проверка токена
token = client.get_token()
print("Токен получен:", token is not None)

# Обычный запрос
result = client.chat([
    {"role": "user", "content": "Привет! Ответь одним словом."}
])
print("Ответ:", result["content"])
print("Токенов:", result["tokens_used"])

# Стриминг
print("\nСтриминг: ", end="", flush=True)
for chunk in client.chat(
    [{"role": "user", "content": "Посчитай от 1 до 5."}],
    stream=True
):
    print(chunk, end="", flush=True)
print()
