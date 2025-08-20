import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode

# Импортируем наш токен из файла конфигурации
from config import BOT_TOKEN
# Импортируем нашу функцию для инициализации БД
from services.database import init_db
# Импортируем все наши роутеры
from handlers import expense_handlers, voice_handlers

# Настраиваем логирование, чтобы видеть информацию о работе бота в консоли
logging.basicConfig(level=logging.INFO)

# Инициализируем бота и диспетчер
# Добавляем parse_mode="HTML" для красивого форматирования текста
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Подключаем роутеры к главному диспетчеру
dp.include_router(expense_handlers.router)
dp.include_router(voice_handlers.router)

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Привет, {message.from_user.full_name}! Я твой бот-секретарь. Готов к работе.")


# Основная функция для запуска бота
async def main():
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