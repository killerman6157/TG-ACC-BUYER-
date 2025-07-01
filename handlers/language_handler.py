# ✅ FILE: handlers/language_handler.py
from aiogram import types
from messages import MESSAGES
from database import update_language, get_user

def register(dp):
    @dp.message_handler(commands=['language'])
    async def set_language(msg: types.Message):
        lang_buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
        lang_buttons.add("English", "Hausa")
        await msg.answer(MESSAGES[get_user(msg.from_user.id)[4]]['language'], reply_markup=lang_buttons)

    @dp.message_handler(lambda m: m.text in ["English", "Hausa"])
    async def save_language(msg: types.Message):
        lang = 'en' if msg.text == "English" else 'ha'
        update_language(msg.from_user.id, lang)
        await msg.answer("✅ Language updated.", reply_markup=types.ReplyKeyboardRemove())
