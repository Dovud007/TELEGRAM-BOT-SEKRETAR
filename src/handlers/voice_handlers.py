import os
import tempfile
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message
from faster_whisper import WhisperModel
from pydub import AudioSegment

# Импортируем наш новый парсер и функцию для работы с БД
from config import FFMPEG_PATH
from services.parser import parse_expense_text
from services.database import add_expense

# Если путь к FFmpeg указан в конфиге, задаем его для pydub
if FFMPEG_PATH:
    AudioSegment.converter = FFMPEG_PATH

router = Router()

MODEL_SIZE = "base"
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

@router.message(F.voice)
async def voice_message_handler(message: Message, bot):
    # Создаем временную директорию для этого конкретного файла
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
            await message.answer("Не удалось распознать речь. Попробуйте еще раз.")
            return

        # ----- ГЛАВНОЕ ИЗМЕНЕНИЕ -----
        # Пытаемся обработать распознанный текст как команду расхода
        parsed_data = parse_expense_text(recognized_text)

        if parsed_data:
            amount, category = parsed_data
            # Если парсер вернул данные, добавляем расход
            add_expense(amount=amount, category=category)
            await message.answer(f"✅ Голосом добавлен расход на сумму **{amount:.2f}** в категории **'{category}'**.")
        else:
            # Если это не команда расхода, просто показываем, что услышали
            await message.answer(f"**Распознанный текст:**\n`{recognized_text}`\n\n_(Не является командой)_")

    except Exception as e:
        await message.answer(f"Произошла ошибка при распознавании речи: {e}")
    finally:
        os.remove(voice_oga_path)
        os.remove(voice_wav_path)