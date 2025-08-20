import asyncio
import logging
import shutil
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties  # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode

# Импортируем наш токен и путь к FFmpeg из файла конфигурации
from config import BOT_TOKEN, FFMPEG_PATH
# Импортируем нашу функцию для инициализации БД
from services.database import init_db
# Импортируем все наши роутеры
from handlers import expense_handlers, voice_handlers

# Настраиваем логирование, чтобы видеть информацию о работе бота в консоли
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
# Добавляем parse_mode="HTML" для красивого форматирования текста
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Подключаем роутеры к главному диспетчеру
dp.include_router(expense_handlers.router)
dp.include_router(voice_handlers.router)

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Привет, {message.from_user.full_name}! Я твой бот-секретарь. Готов к работе.")

def check_ffmpeg():
    """Проверяет, доступен ли FFmpeg в системе."""
    # Проверяем путь из .env файла
    if FFMPEG_PATH and os.path.isfile(FFMPEG_PATH):
        logging.info(f"FFmpeg найден по указанному пути: {FFMPEG_PATH}")
        return True

    # Если в .env не указано, ищем в системном PATH
    if shutil.which("ffmpeg"):
        logging.info("FFmpeg найден в системном PATH. Для pydub будет использована эта версия.")
        return True

    # Если FFmpeg не найден нигде
    logging.critical("!!! ВНИМАНИЕ: FFmpeg не найден !!!")
    logging.critical("Для обработки голосовых сообщений боту необходим FFmpeg.")
    logging.critical("Пожалуйста, установите FFmpeg и либо добавьте его в системный PATH,")
    logging.critical("либо укажите полный путь к исполняемому файлу в файле .env (переменная FFMPEG_PATH).")
    return False

# Основная функция для запуска бота
async def main():
    # Перед запуском проверяем, доступен ли FFmpeg
    if not check_ffmpeg():
        return  # Завершаем работу, если FFmpeg не найден

    # Вызываем функцию инициализации базы данных перед запуском бота
    init_db()
    
    # Запускаем обработку входящих сообщений
    await dp.start_polling(bot)


# --- ЭТО САМЫЙ ВАЖНЫЙ БЛОК ---
# Он запускает выполнение функции main
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")