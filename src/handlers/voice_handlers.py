import os
import tempfile
from pathlib import Path
import json
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from faster_whisper import WhisperModel
from pydub import AudioSegment

# Импортируем новый парсер на базе LLM и функцию для работы с БД
from config import FFMPEG_PATH
from services.vertex_ai import parse_expense_with_llm
from services.database import add_expense

# Если путь к FFmpeg указан в конфиге, задаем его для pydub
if FFMPEG_PATH:
    AudioSegment.converter = FFMPEG_PATH

router = Router()

MODEL_SIZE = "medium"
# Note: The first time a model is used, it will be downloaded.
# The "medium" model is a few hundred MBs, so the first voice message
# after a restart might take a bit longer to process.
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def create_confirmation_keyboard(data: dict) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками Да/Нет для подтверждения расхода."""
    # Мы не можем передать целый словарь в callback_data, поэтому сериализуем его в JSON
    # и убедимся, что он не слишком длинный.
    # Более надежный способ - хранить временные данные в кэше (например, Redis)
    # и передавать только уникальный ключ. Но для простоты пока так.

    # Убираем confirmation_message, чтобы не передавать лишнего
    callback_data = data.copy()
    callback_data.pop('confirmation_message', None)

    # Ограничиваем длину категории, чтобы не превысить лимит callback_data
    if len(callback_data['category']) > 20:
        callback_data['category'] = callback_data['category'][:20]

    yes_callback = json.dumps(callback_data)

    buttons = [
        [
            InlineKeyboardButton(text="✅ Да, все верно", callback_data=f"confirm_expense:yes:{yes_callback}"),
            InlineKeyboardButton(text="❌ Нет, уточнить", callback_data="confirm_expense:no")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.voice)
async def voice_message_handler(message: Message, bot):
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

        if parsed_data and parsed_data.get('amount'):
            # Если LLM вернул данные, запрашиваем подтверждение
            keyboard = create_confirmation_keyboard(parsed_data)
            await message.answer(
                text=parsed_data['confirmation_message'],
                reply_markup=keyboard
            )
        else:
            # Если LLM не смог распознать расход
            await message.answer(
                "Я вас услышал, но не смог распознать это как команду на запись расхода.\n"
                f"**Распознанный текст:** `{recognized_text}`\n\n"
                "Пожалуйста, уточните, что вы имели в виду, или скажите о расходе более явно."
            )

    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке голосового сообщения: {e}")
    finally:
        os.remove(voice_oga_path)
        os.remove(voice_wav_path)