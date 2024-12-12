import configparser
import transcribe.stt as stt
import linkcheck.main as linkcheck
import json
from typing import Union

import asyncio

from aiogram import Router, Bot, Dispatcher, F, types
from aiogram.filters.command import Command
import logging

from database import Messagesx

Messagesx.create_db()

router = Router(name=__name__)

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser()
config.read("config.ini")

TOKEN = config["main"]["bot_token"]
USER_ID = config["main"]["user"]

bot = Bot(token=TOKEN)

async def send_msg(message_old: str, message_new: Union[str, None], user_fullname: str, user_id: int, bot: Bot):
    if message_new is None:
        msg = (f' <b>Пользователь {user_fullname} ({user_id})</b>\n'
               f' <b>Сообщение удалено</b>\n'
               f' Сообщение:\n<code>{message_old}</code>\n')
    else:
        msg = (f' <b>Пользователь {user_fullname} ({user_id})</b>\n'
               f' <b>Сообщение изменено:</b>\n'
               f' Старое сообщение:\n<code>{message_old}</code>\n'
               f' Новое сообщение:\n<code>{message_new}</code>')
    await bot.send_message(510443335, msg, parse_mode='html')

# Функция для обработки голосового сообщения
@router.business_message(F.voice)
async def voice_processing(message: types.Message):
    await stt.voice_processing(message, bot, business_connection_id=message.business_connection_id)

# Функция для обработки текстового сообщения содержащего ссылку
@router.business_message(F.text.regexp(r'(https?:\/\/|www\.)[^\s]+(\.[a-z]{2,6})[^\s]*'))
async def echo(message: types.Message):
    if linkcheck.predict(message.text) != "legitimate":
        await bot.send_message(message.from_user.id, text="Malicious❗", business_connection_id=message.business_connection_id) #type: ignore
    else:
        await bot.send_message(message.from_user.id, text="Safe ✅", business_connection_id=message.business_connection_id) #type: ignore

@router.business_message(F.text)
async def business_message(message: types.Message):
    if message.from_user.id == message.chat.id:#type: ignore
        user_msg = Messagesx.get(user_id=message.from_user.id)#type: ignore
        data = {message.message_id: message.text}
        if user_msg is None:
            Messagesx.add(user_id=message.from_user.id, message_history=json.dumps(data))#type: ignore
        else:
            msg_history = json.loads(user_msg.message_history)
            data = {**msg_history, **data}
            Messagesx.update(user_id=message.from_user.id, message_history=json.dumps(data))#type: ignore

@router.edited_business_message()
async def edited_business_message(message: types.Message):
    if message.from_user.id == message.chat.id: #type: ignore
        user_msg = Messagesx.get(user_id=message.from_user.id)#type: ignore
        data = {message.message_id: message.text}
        if user_msg is None:
            Messagesx.add(user_id=message.from_user.id, message_history=json.dumps(data)) #type: ignore
        else:
            msg_history = json.loads(user_msg.message_history)
            if str(message.message_id) in msg_history:
                await send_msg(message_old=msg_history[str(message.message_id)], message_new=message.text,
                               user_fullname=message.from_user.full_name, user_id=message.chat.id, bot=message.bot)#type: ignore
                data = {**msg_history, **data}
                Messagesx.update(user_id=message.from_user.id, message_history=json.dumps(data))#type: ignore

@router.deleted_business_messages()
async def deleted_business_message(message: types.BusinessMessagesDeleted):
    user_msg = Messagesx.get(user_id=message.chat.id)
    if user_msg is not None:
        msg_history = json.loads(user_msg.message_history)
        for msg_id in message.message_ids:
            if str(msg_id) in msg_history:
                await send_msg(message_old=msg_history[str(msg_id)], message_new=None,
                               user_fullname=message.chat.full_name, user_id=message.chat.id, bot=message.bot) # type: ignore
                msg_history.pop(str(msg_id))
                Messagesx.update(user_id=message.chat.id, message_history=json.dumps(msg_history))


# ! Simple Messagesx

@router.message(F.voice)
async def voice(message: types.Message):
    await stt.voice_processing_b(message, bot)

@router.message(F.text.regexp(r'(https?:\/\/|www\.)[^\s]+(\.[a-z]{2,6})[^\s]*'))
async def links(message: types.Message):
    if linkcheck.predict(message.text) != "legitimate":
        await bot.send_message(message.from_user.id, text="Malicious❗") #type: ignore
    else:
        await bot.send_message(message.from_user.id, text="Safe ✅") #type: ignore


@router.message(Command("start"))
async def start(message: types.Message):
    await bot.send_message(message.chat.id, str(message.chat.id))

async def main() -> None:

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

asyncio.run(main())
