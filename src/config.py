import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота. Если токен не найден, будет ошибка.
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("Ошибка: не найден токен бота. Убедитесь, что он задан в файле .env")
    exit()