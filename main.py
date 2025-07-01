import os
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

from database import init_db
from handlers import otp_handler, cancel_handler, balance_handler, withdraw_handler, language_handler, admin_handler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

init_db()

otp_handler.register(dp)
cancel_handler.register(dp)
balance_handler.register(dp)
withdraw_handler.register(dp)
language_handler.register(dp)
admin_handler.register(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
