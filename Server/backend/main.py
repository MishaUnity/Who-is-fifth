import os
from gigachat import GigaChatClient

# Задайте переменные окружения перед запуском
os.environ["GIGACHAT_AUTH_KEY"] = "MDE5ZDJhNTktMzg2YS03ZDM0LThmMTUtMWIyNTM5ZDNjNzA0OjQwYjhmNjFhLWJiM2EtNGU4Ni04MzE1LTJmOWU3MjNhMTZlYQ=="
os.environ["GIGACHAT_MODEL"] = "GigaChat"

client = GigaChatClient()

# 1. Проверка получения токена
token = client.get_token()
print("Токен получен:", token is not None)

# 2. Обычный запрос
result = client.chat([
    {"role": "user", "content": "Привет! Ответь одним словом."}
])
print("Ответ:", result["content"])
print("Токенов использовано:", result["tokens_used"])

# 3. Стриминг
print("\nСтриминг: ", end="", flush=True)
for chunk in client.chat(
    [{"role": "user", "content": "Посчитай от 1 до 5."}],
    stream=True
):
    print(chunk, end="", flush=True)
print()