import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота. Если токен не найден, будет ошибка.
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("Ошибка: не найден токен бота. Убедитесь, что он задан в файле .env")
    exit()

# --- Настройка для конвертации аудио ---
# Укажите здесь путь к исполняемому файлу ffmpeg.exe
# Pydub использует FFmpeg для конвертации аудиофайлов (например, из .oga в .wav)
#
# Windows: "C:\\path\\to\\ffmpeg\\bin\\ffmpeg.exe" (обратите внимание на двойные слэши)
# Linux/macOS: "/usr/bin/ffmpeg" (можно найти с помощью команды `which ffmpeg`)
#
# Если FFmpeg находится в системном PATH, можно оставить значение пустым (None)
FFMPEG_PATH = os.getenv('FFMPEG_PATH')