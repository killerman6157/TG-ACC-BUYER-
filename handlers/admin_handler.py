# ✅ FILE: handlers/admin_handler.py
from aiogram import types
import os
from database import get_stats
from dotenv import load_dotenv
load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))

def register(dp):
    @dp.message_handler(commands=['admin'])
    async def admin_panel(msg: types.Message):
        if msg.from_user.id != ADMIN_ID:
            return await msg.answer("Access denied.")

        users, verified, unverified = get_stats()
        await msg.answer(f"👥 Users: {users}\n✅ Verified: {verified}\n❌ Unverified: {unverified}")
