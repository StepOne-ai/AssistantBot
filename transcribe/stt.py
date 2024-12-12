from aiogram.types.message import Message
import speech_recognition as sr
import aiohttp
from pydub import AudioSegment

async def download_file(url, save_path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(save_path, 'wb') as new_file:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        new_file.write(chunk)

def va_transcribe():
    sound = AudioSegment.from_ogg("new_file.ogg")
    sound.export("transcript.wav", format="wav")

    AUDIO_FILE = "transcript.wav"

    r = sr.Recognizer()
    with sr.AudioFile(AUDIO_FILE) as source:
        audio = r.record(source)
        res = r.recognize_vosk(audio, language="ru-RU")
        return res


async def voice_processing(message, bot, business_connection_id):
    # sent = bot.send_message(message.from_user.id, text="Обрабатываю...", business_connection_id=business_connection_id)
    file_info = await bot.get_file(message.voice.file_id)
    file_path = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

    # Download the file asynchronously
    await download_file(file_path, 'new_file.ogg')

    # Assuming va_transcribe needs to be run synchronously
    res = va_transcribe()[14:-3]

    msg = (f'<b>Вот, что получилось: </b>\n'
            f'<code>{res}</code>')

    # await bot.delete_message(message.from_user.id, sent.message_id)
    await bot.send_message(message.from_user.id, text=msg, parse_mode='html', business_connection_id=business_connection_id)


async def voice_processing_b(message, bot):
    sent: Message = await bot.send_message(message.from_user.id, text="Обрабатываю...")
    file_info = await bot.get_file(message.voice.file_id)
    file_path = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

    # Download the file asynchronously
    await download_file(file_path, 'new_file.ogg')

    # Assuming va_transcribe needs to be run synchronously
    res = va_transcribe()[14:-3]

    msg = (f'<b>Вот, что получилось: </b>\n'
            f'<code>{res}</code>')

    await bot.delete_message(message.from_user.id, sent.message_id)
    await bot.send_message(message.from_user.id, text=msg, parse_mode='html')
