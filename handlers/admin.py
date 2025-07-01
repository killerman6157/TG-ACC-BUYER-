from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from config import ADMIN_ID, CHANNEL_ID
from utils import database

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

@router.message(Command("user_accounts"))
async def user_accounts_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) != 2:
        return await message.answer("⚠ Amfani: /user_accounts [UserID]")

    user_id = int(args[1])
    count = database.count_user_accounts(user_id)

    await message.answer(
        f"👤 User ID: {user_id} yana da account(s) guda {count} da aka karɓa.\n"
        "✅ Wadannan sun cancanci biyan kuɗi."
    )

@router.message(Command("mark_paid"))
async def mark_paid_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) != 3:
        return await message.answer("⚠ Amfani: /mark_paid [UserID] [Adadin]")

    user_id = int(args[1])
    amount = int(args[2])
    database.mark_accounts_paid(user_id, amount)

    await message.answer(
        f"✅ An tabbatar da biyan user ID: {user_id} don accounts {amount}."
    )

@router.message(Command("completed_today_payment"))
async def completed_today_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.bot.send_message(
        CHANNEL_ID,
        "📢 <b>SANARWA:</b> An biya duk wanda ya nemi kuɗi yau!\n"
        "Muna fatan alheri. Sai gobe karfe 8:00 AM. ✅"
    )
    await message.answer("📬 An tura sanarwa zuwa channel.")
