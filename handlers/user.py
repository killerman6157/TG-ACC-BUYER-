from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, time
from config import ADMIN_ID, CHANNEL_ID, TIMEZONE
from utils import database
from aiogram.utils.keyboard import InlineKeyboardBuilder
import pytz

router = Router()

class BuyerState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_otp = State()
    waiting_for_withdraw_info = State()

def is_within_time():
    now = datetime.now(pytz.timezone(TIMEZONE)).time()
    return time(8, 0) <= now <= time(22, 0)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    if not is_within_time():
        return await message.answer(
            "🚫 An rufe karɓar Telegram accounts na yau.\nZa a bude gobe 8:00 na safe (WAT)."
        )

    await state.set_state(BuyerState.waiting_for_phone)
    await message.answer(
        "📥 Turo lambar wayar account ɗin da kake son siyarwa (misali: +2348167757987).\n"
        "🛡 Tabbatar ka cire 2FA kafin tura.",
    )

@router.message(BuyerState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()

    if database.phone_exists(phone):
        return await message.answer(
            f"⚠️ An riga an karɓi wannan lambar: {phone}\n"
            "⏳ Za ka iya sake turawa bayan mako ɗaya."
        )

    database.save_account(message.from_user.id, phone)
    await state.update_data(phone=phone)
    await state.set_state(BuyerState.waiting_for_otp)

    await message.answer(
        f"✅ An tura OTP zuwa {phone}.\n\n📩 Turo lambar OTP ɗin a nan."
    )

@router.message(BuyerState.waiting_for_otp)
async def process_otp(message: Message, state: FSMContext):
    data = await state.get_data()
    phone = data.get("phone")

    # Log OTP reception (can log/save if needed)
    await state.clear()

    await message.answer(
        f"✅ An shiga account ɗin {phone} cikin nasara.\n"
        "💵 Za a biya daga 8:00 na dare (WAT). Ka shirya cire kuɗi da /withdraw"
    )

@router.message(Command("withdraw"))
async def withdraw(message: Message, state: FSMContext):
    if not is_within_time():
        return await message.answer(
            "🚫 An rufe biyan kuɗi na yau. Za a buɗe gobe 8:00 AM (WAT)."
        )

    await state.set_state(BuyerState.waiting_for_withdraw_info)
    await message.answer(
        "💳 Turo lambar asusun bankinka da sunan mai asusun.\n"
        "Misali: 9131085651 OPay Bashir Rabiu"
    )

@router.message(BuyerState.waiting_for_withdraw_info)
async def save_withdraw_info(message: Message, state: FSMContext):
    info = message.text.strip()
    database.save_withdrawal(message.from_user.id, info)
    await state.clear()

    await message.answer("✅ Bukatar cire kuɗi ta karɓu. Ana jira admin.")

    # Notify admin
    accounts = database.get_user_accounts(message.from_user.id)
    await message.bot.send_message(
        ADMIN_ID,
        f"💰 BUKATAR BIYA!\n"
        f"👤 User: {message.from_user.id} (@{message.from_user.username})\n"
        f"📱 Accounts: {', '.join(accounts)}\n"
        f"🏦 Bank Info: {info}\n"
        f"/mark_paid {message.from_user.id} {len(accounts)}"
    )

@router.message(Command("language"))
async def choose_language(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🇳🇬 Hausa", callback_data="lang_hausa")
    builder.button(text="🇬🇧 English", callback_data="lang_english")
    await message.answer("🌐 Zaɓi harshenka / Choose your language:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("lang_"))
async def set_language(call: CallbackQuery):
    lang = call.data.split("_")[1]
    database.set_user_lang(call.from_user.id, lang)
    await call.answer("✅ Language updated.")
    await call.message.edit_text("🌍 Harshen ka ya canza / Language set.")

@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ An soke aikin.")
