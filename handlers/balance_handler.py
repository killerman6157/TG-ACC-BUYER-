# ✅ FILE: handlers/balance_handler.py
from aiogram import types
from database import get_user
from messages import MESSAGES

def register(dp):
    @dp.message_handler(commands=['account_balance'])
    async def account_balance(msg: types.Message):
        user = get_user(msg.from_user.id)
        lang = user[4]
        txt = MESSAGES[lang]['balance'].format(user=user[0], v=user[1], u=user[2], bal=user[3])
        await msg.answer(txt)
