# ✅ FILE: handlers/withdraw_handler.py
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from messages import MESSAGES
from database import get_user

class WithdrawState(StatesGroup):
    choosing_method = State()
    waiting_details = State()

def register(dp):
    @dp.message_handler(commands=['withdraw'])
    async def withdraw(msg: types.Message):
        lang = get_user(msg.from_user.id)[4]
        await msg.answer(MESSAGES[lang]['withdraw_method'])
        await WithdrawState.choosing_method.set()

    @dp.message_handler(state=WithdrawState.choosing_method)
    async def choose_method(msg: types.Message, state: FSMContext):
        await state.update_data(method=msg.text.strip())
        lang = get_user(msg.from_user.id)[4]
        await msg.answer(MESSAGES[lang]['send_account'])
        await WithdrawState.waiting_details.set()

    @dp.message_handler(state=WithdrawState.waiting_details)
    async def receive_details(msg: types.Message, state: FSMContext):
        await msg.answer(MESSAGES[get_user(msg.from_user.id)[4]]['withdraw_done'])
        await state.finish()
