import re
import os
import tempfile
from pathlib import Path
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from faster_whisper import WhisperModel
from pydub import AudioSegment

from services.database import add_expense
from services.parser import parse_expense_text
from states import ExpenseConversation

router = Router()

# Модель для распознавания речи (можно вынести в отдельный сервис, но для простоты пока здесь)
model = WhisperModel("medium", device="cpu", compute_type="int8")

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

@router.message(ExpenseConversation.waiting_for_amounts, F.voice)
async def handle_amounts_voice(message: Message, state: FSMContext, bot):
    """
    Handles the voice message with amounts for the multi-step expense entry.
    """
    await message.answer("🎤 Распознаю суммы...")

    # --- Блок распознавания речи (аналогично voice_handlers.py) ---
    voice_dir = Path(tempfile.gettempdir()) / "secretary_bot_voices"
    voice_dir.mkdir(exist_ok=True)
    voice_file_info = await bot.get_file(message.voice.file_id)
    voice_oga_path = voice_dir / f"{message.voice.file_id}.oga"
    await bot.download_file(voice_file_info.file_path, destination=voice_oga_path)
    voice_wav_path = voice_dir / f"{message.voice.file_id}.wav"
    AudioSegment.from_file(voice_oga_path).export(voice_wav_path, format="wav")

    try:
        segments, _ = model.transcribe(str(voice_wav_path), beam_size=5, language="ru")
        recognized_text = "".join(segment.text for segment in segments).strip()

        if not recognized_text:
            await message.answer("Не удалось распознать речь. Попробуйте еще раз.")
            return

        # --- Логика извлечения сумм и сохранения ---
        # Ищем все числа в распознанном тексте
        amounts = [float(num) for num in re.findall(r'\d+(?:\.\d+)?', recognized_text)]

        user_data = await state.get_data()
        dates = user_data.get("dates", [])
        category = user_data.get("category")

        if len(amounts) != len(dates):
            await message.answer(
                f"Я ожидал {len(dates)} сумм, но вы назвали {len(amounts)}. "
                "Давайте попробуем еще раз. Пожалуйста, назовите суммы для каждой даты."
            )
            # Не сбрасываем состояние, даем пользователю еще попытку
            return

        # Сохраняем все расходы
        for i, date_str in enumerate(dates):
            # В базе данных дата сохранится с текущим временем, а не с указанной датой.
            # Это ограничение текущей схемы БД, для исправления потребуется миграция.
            # Пока что для простоты добавляем все сегодняшним числом.
            add_expense(amount=amounts[i], category=f"{category} ({date_str})")

        await message.answer(
            f"✅ Готово! Успешно добавил {len(amounts)} записей о расходах в категорию '{category}'."
        )

    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке сумм: {e}")
    finally:
        # Очищаем состояние в любом случае
        await state.clear()
        os.remove(voice_oga_path)
        os.remove(voice_wav_path)