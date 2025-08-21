import os
import tempfile
from pathlib import Path
import json
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from faster_whisper import WhisperModel
from pydub import AudioSegment

# Импортируем новый парсер на базе LLM и функцию для работы с БД
from config import FFMPEG_PATH
from services.vertex_ai import parse_expense_with_llm
from services.database import add_expense
from states import ExpenseConversation

# Если путь к FFmpeg указан в конфиге, задаем его для pydub
if FFMPEG_PATH:
    AudioSegment.converter = FFMPEG_PATH

router = Router()

MODEL_SIZE = "medium"
# Note: The first time a model is used, it will be downloaded.
# The "medium" model is a few hundred MBs, so the first voice message
# after a restart might take a bit longer to process.
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

from services.cache import temp_data_cache

def create_confirmation_keyboard(data: dict) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопками Да/Нет для подтверждения расхода.
    Использует кэш для временного хранения данных.
    """
    # Убираем confirmation_message, т.к. оно не нужно для сохранения
    callback_data = data.copy()
    callback_data.pop('confirmation_message', None)

    # Сохраняем данные в кэш и получаем уникальный ключ
    data_key = temp_data_cache.set(callback_data)

    # Теперь callback_data содержит только короткий и безопасный ключ
    yes_callback_data = f"confirm_expense:yes:{data_key}"

    buttons = [
        [
            InlineKeyboardButton(text="✅ Да, все верно", callback_data=yes_callback_data),
            InlineKeyboardButton(text="❌ Нет, уточнить", callback_data="confirm_expense:no")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.voice)
async def voice_message_handler(message: Message, bot, state: FSMContext):
    await message.answer("🎤 Услышал вас, начинаю распознавание...")

    voice_dir = Path(tempfile.gettempdir()) / "secretary_bot_voices"
    voice_dir.mkdir(exist_ok=True)
    voice_file_info = await bot.get_file(message.voice.file_id)
    voice_oga_path = voice_dir / f"{message.voice.file_id}.oga"
    await bot.download_file(voice_file_info.file_path, destination=voice_oga_path)
    voice_wav_path = voice_dir / f"{message.voice.file_id}.wav"
    AudioSegment.from_file(voice_oga_path).export(voice_wav_path, format="wav")

    try:
        segments, info = model.transcribe(str(voice_wav_path), beam_size=5, language="ru")
        recognized_text = "".join(segment.text for segment in segments).strip()

        if not recognized_text:
            await message.answer("Не удалось распознать речь в аудио. Попробуйте еще раз.")
            return

        # Отправляем текст в LLM для анализа
        parsed_data = parse_expense_with_llm(recognized_text)
        intent = parsed_data.get("intent") if parsed_data else None

        if intent == "add_expense":
            # Если LLM распознал команду на добавление расхода
            keyboard = create_confirmation_keyboard(parsed_data)
            await message.answer(
                text=parsed_data['confirmation_message'],
                reply_markup=keyboard
            )
        elif intent == "get_report":
            # Если LLM распознал команду на получение отчета
            from . import report_handlers
            await report_handlers.handle_report_request(message, parsed_data)

        elif intent == "add_expense_incomplete":
            # Если LLM распознал неполную команду на добавление расхода
            # Сохраняем частичные данные в FSM
            await state.update_data(
                category=parsed_data.get("category"),
                dates=parsed_data.get("dates")
            )
            # Задаем уточняющий вопрос и показываем кастомные кнопки
            clarification_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎤 Озвучить суммы", callback_data="provide_amounts")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_fsm")]
            ])
            await message.answer(
                text=parsed_data.get("clarification_question", "Пожалуйста, уточните детали."),
                reply_markup=clarification_keyboard
            )
            # Устанавливаем состояние ожидания сумм
            await state.set_state(ExpenseConversation.waiting_for_amounts)

        else:
            # Если LLM не смог распознать намерение
            await message.answer(
                "Я вас услышал, но не смог распознать это как известную мне команду.\n"
                f"**Распознанный текст:** `{recognized_text}`\n\n"
                "Пожалуйста, попробуйте переформулировать."
            )

    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке голосового сообщения: {e}")
    finally:
        os.remove(voice_oga_path)
        os.remove(voice_wav_path)