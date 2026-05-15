from gigachat import GigaChatClient

from dotenv import load_dotenv
from pathlib import Path
import os


env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


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
