from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.database import add_expense
# Импортируем наш универсальный парсер
from services.parser import parse_expense_text

router = Router()

@router.message(Command("expense"))
async def add_expense_handler(message: Message):
    """
    Обработчик команды /expense, использующий универсальный парсер.
    """
    parsed_data = parse_expense_text(message.text)
    
    if parsed_data:
        amount, category = parsed_data
        add_expense(amount=amount, category=category)
        await message.answer(f"✅ Расход на сумму **{amount:.2f}** в категории **'{category}'** успешно добавлен.")
    else:
        # Если формат команды неправильный, парсер вернет None
        await message.answer(
            "❌ **Ошибка!** Неправильный формат команды.\n"
            "Используйте: `/expense <сумма> <категория>`\n\n"
            "Например: `/expense 500 Обед`"
        )