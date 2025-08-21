import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from services.database import get_expenses_for_period
from services.excel_report import create_excel_report
import os

router = Router()

async def handle_report_request(message: Message, parsed_data: dict):
    """
    Handles a request to generate an expense report.
    """
    try:
        start_date_str = parsed_data.get("start_date")
        end_date_str = parsed_data.get("end_date")

        if not start_date_str or not end_date_str:
            await message.answer("К сожалению, я не смог определить период для отчета. Попробуйте еще раз.")
            return

        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        # Add time component to end_date to include the whole day
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

        await message.answer(f"Готовлю отчет по расходам за период с {start_date_str} по {end_date_str}...")

        # Get expenses from the database
        expenses = get_expenses_for_period(start_date, end_date)

        if not expenses:
            await message.answer("За указанный период не найдено ни одной записи о расходах.")
            return

        # Генерируем Excel-файл
        report_path = create_excel_report(expenses)

        try:
            # Отправляем файл пользователю
            await message.answer_document(
                FSInputFile(report_path),
                caption="Ваш отчет по расходам готов."
            )
        finally:
            # Удаляем временный файл после отправки, даже если отправка не удалась.
            # Блок finally гарантирует, что эта строка выполнится после завершения await.
            os.remove(report_path)

    except Exception as e:
        # Этот блок теперь будет ловить ошибки, не связанные с отправкой файла
        # (например, ошибки при конвертации дат или получении данных из БД)
        await message.answer(f"Произошла ошибка при подготовке данных для отчета: {e}")
