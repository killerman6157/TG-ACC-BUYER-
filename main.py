# main.py
import os
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import PhoneNumberInvalidError, PhoneCodeInvalidError, SessionPasswordNeededError, FloodWaitError
from telethon.tl.functions.users import GetFullUserRequest

import aiosqlite # Import aiosqlite

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Configuration Variables ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID')) # Channel for admin notifications

# Database file name
DB_NAME = 'bot_data.db'

# Check if essential variables are loaded
if not all([BOT_TOKEN, API_ID, API_HASH, ADMIN_ID, CHANNEL_ID]):
    logger.error("Missing one or more essential environment variables. Please check your .env file.")
    exit(1)

# --- Bot and Dispatcher Setup ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FSM States for Account Selling Process ---
class SellAccountStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_otp = State()
    waiting_for_2fa = State() # For accounts with 2FA enabled

# --- FSM States for Withdrawal Process ---
class WithdrawStates(StatesGroup):
    waiting_for_bank_details = State()

# --- Account Receiving Status (Open/Closed) ---
account_receiving_open = True # Default to open
payment_processing_open = True # Default to open

# --- Keyboard Buttons ---
cancel_button = KeyboardButton(text="/cancel")
cancel_keyboard = ReplyKeyboardMarkup(keyboard=[[cancel_button]], resize_keyboard=True)

# --- Database Functions ---

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Table for accounts submitted by users
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phone_number TEXT NOT NULL UNIQUE,
                session_path TEXT NOT NULL,
                status TEXT NOT NULL, -- e.g., 'pending_otp', 'pending_2fa', 'ready_for_payment', 'paid'
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Table for withdrawal requests
        await db.execute('''
            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                bank_details TEXT NOT NULL,
                num_accounts INTEGER NOT NULL,
                accounts_list TEXT NOT NULL, -- comma-separated phone numbers
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_paid BOOLEAN DEFAULT FALSE
            )
        ''')
        # Table for number cooldown (to prevent re-submission within a week)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS number_cooldown (
                phone_number TEXT PRIMARY KEY,
                last_accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()
    logger.info("Database initialized successfully.")

async def add_user_account(user_id, phone_number, session_path, status='pending_otp'):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO user_accounts (user_id, phone_number, session_path, status) VALUES (?, ?, ?, ?)",
            (user_id, phone_number, session_path, status)
        )
        await db.commit()
    logger.info(f"Added account {phone_number} for user {user_id} with status {status}.")

async def update_account_status(phone_number, new_status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE user_accounts SET status = ? WHERE phone_number = ?",
            (new_status, phone_number)
        )
        await db.commit()
    logger.info(f"Updated status of account {phone_number} to {new_status}.")

async def get_user_accounts_for_payment(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT phone_number FROM user_accounts WHERE user_id = ? AND status = 'ready_for_payment'",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows] # Return list of phone numbers

async def get_account_status(phone_number):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT status FROM user_accounts WHERE phone_number = ?",
            (phone_number,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def add_withdrawal_request(user_id, username, bank_details, num_accounts, accounts_list):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO withdrawal_requests (user_id, username, bank_details, num_accounts, accounts_list) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, bank_details, num_accounts, accounts_list)
        )
        await db.commit()
    logger.info(f"Added withdrawal request for user {user_id}.")

async def mark_accounts_as_paid(user_id, phone_numbers):
    async with aiosqlite.connect(DB_NAME) as db:
        # Update status of specific phone numbers
        for phone in phone_numbers:
            await db.execute(
                "UPDATE user_accounts SET status = 'paid' WHERE user_id = ? AND phone_number = ?",
                (user_id, phone)
            )
        # Mark pending withdrawal requests as paid if applicable
        # This assumes a user only has one pending withdrawal at a time for 'ready_for_payment' accounts
        await db.execute(
            "UPDATE withdrawal_requests SET is_paid = TRUE WHERE user_id = ? AND is_paid = FALSE",
            (user_id,)
        )
        await db.commit()
    logger.info(f"Marked accounts {phone_numbers} for user {user_id} as paid.")

async def get_total_user_accounts(user_id, status=None):
    async with aiosqlite.connect(DB_NAME) as db:
        if status:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM user_accounts WHERE user_id = ? AND status = ?",
                (user_id, status)
            )
        else:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM user_accounts WHERE user_id = ?",
                (user_id,)
            )
        row = await cursor.fetchone()
        return row[0] if row else 0

async def add_number_to_cooldown(phone_number):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO number_cooldown (phone_number, last_accepted_at) VALUES (?, CURRENT_TIMESTAMP)",
            (phone_number,)
        )
        await db.commit()
    logger.info(f"Added {phone_number} to cooldown.")

async def is_number_on_cooldown(phone_number):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT last_accepted_at FROM number_cooldown WHERE phone_number = ?",
            (phone_number,)
        )
        row = await cursor.fetchone()
        if row:
            last_accepted_str = row[0]
            # Convert string timestamp from DB to datetime object, assuming it's UTC or local
            # Better to store and retrieve as UTC to avoid timezone issues.
            # SQLite stores TIMESTAMP as TEXT by default. We'll parse it.
            # Example format: 2025-07-01 17:18:41
            last_accepted_at = datetime.strptime(last_accepted_str, '%Y-%m-%d %H:%M:%S')
            
            # Assuming DB stores UTC and we convert to WAT for comparison
            # Or simpler: just compare timedeltas in UTC, which is what CURRENT_TIMESTAMP does.
            # Let's assume CURRENT_TIMESTAMP is system time, and we check against that.
            
            # Define cooldown period (7 days)
            cooldown_period = timedelta(days=7)
            
            # Check if current time is within cooldown period from last_accepted_at
            if datetime.now() - last_accepted_at < cooldown_period:
                return True
        return False

# --- Handlers for User (Seller) ---

@dp.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"User {user_id} started the bot.")
    await state.clear() # Clear any previous state

    welcome_message = (
        "Barka da zuwa cibiyar karbar Telegram accounts! Don farawa, turo lambar wayar account din "
        "da kake son sayarwa (misali: +2348167757987). "
        "Tabbatar ka cire Two-Factor Authentication (2FA) kafin ka tura."
    )
    await message.reply(welcome_message, reply_markup=cancel_keyboard)
    await state.set_state(SellAccountStates.waiting_for_phone)

@dp.message(Command('cancel'))
async def handle_cancel(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    if current_state:
        logger.info(f"User {user_id} cancelled operation from state {current_state}.")
        await state.clear()
        await message.reply("An soke aikin cikin nasara.", reply_markup=ReplyKeyboardRemove())
        # Also clean up Telethon client if it was in state
        data = await state.get_data()
        client = data.get('telethon_client')
        if client and client.is_connected():
            await client.disconnect()
            logger.info(f"Telethon client disconnected for user {user_id} after cancel.")
    else:
        await message.reply("Babu wani aiki da ake yi don sokewa.", reply_markup=ReplyKeyboardRemove())


@dp.message(SellAccountStates.waiting_for_phone)
async def process_phone_number(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    phone_number = message.text.strip()

    # Basic phone number validation (more robust validation can be added)
    if not (phone_number.startswith('+') and phone_number[1:].isdigit() and len(phone_number) > 7):
        await message.reply("Don Allah ka tura lambar waya da ta dace, farawa da alamar ƙari (+). Misali: +2348167757987")
        return

    # Check if account receiving is open
    if not account_receiving_open:
        await message.reply(
            "An rufe karbar Telegram accounts na yau. An rufe karbar accounts da karfe 10:00 na dare (WAT). "
            "Za a sake buɗewa gobe karfe 8:00 na safe. Don Allah a gwada gobe."
        )
        await state.clear()
        return

    # Check cooldown for this number from DB
    if await is_number_on_cooldown(phone_number):
        await message.reply(
            f"⚠️ Kuskure! An riga an yi rajistar wannan lambar!\n"
            f"{phone_number}\n"
            f"Ba za ka iya sake tura wannan lambar ba sai nan da mako ɗaya."
        )
        await state.clear()
        return
        
    # Check if this number is already in user_accounts table and not 'paid' or too old
    existing_account_status = await get_account_status(phone_number)
    if existing_account_status and existing_account_status != 'paid': # If it's anything but 'paid', it's active
        await message.reply(
            f"⚠️ Kuskure! An riga an yi rajistar wannan lambar!\n"
            f"{phone_number}\n"
            f"Ba za ka iya sake tura wannan lambar ba sai nan da mako ɗaya."
        )
        await state.clear()
        return

    await message.reply("Ana sarrafawa... Don Allah a jira.")
    await state.update_data(current_phone=phone_number)

    # Ensure sessions directory exists
    session_dir = 'sessions'
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)

    client_session_path = f"{session_dir}/{phone_number.replace('+', '')}" # Telethon adds .session
    client = TelegramClient(client_session_path, API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            logger.info(f"Attempting to send code to {phone_number} for user {user_id}.")
            # Telethon's send_code_request requires a connection.
            await client.send_code_request(phone_number)
            await message.reply(
                f"🇳🇬 An tura lambar sirri (OTP) zuwa lambar: {phone_number}. Don Allah ka tura lambar sirrin a nan.",
                reply_markup=cancel_keyboard
            )
            await state.set_state(SellAccountStates.waiting_for_otp)
            await state.update_data(telethon_client=client, client_session_path=client_session_path)
            # Add to DB with pending_otp status
            await add_user_account(user_id, phone_number, client_session_path + '.session', 'pending_otp')
        else:
            # This case means the session file already exists and is authorized.
            # This indicates the account was previously successfully taken.
            logger.warning(f"Session for {phone_number} already authorized during initial check for user {user_id}. Treating as re-submission.")
            await message.reply(
                f"⚠️ Kuskure! An riga an yi rajistar wannan lambar!\n"
                f"{phone_number}\n"
                f"Ba za ka iya sake tura wannan lambar ba sai nan da mako ɗaya."
            )
            await state.clear()
            await client.disconnect() # Disconnect the client
            await add_number_to_cooldown(phone_number) # Add to cooldown in DB


    except PhoneNumberInvalidError:
        logger.error(f"Invalid phone number {phone_number} for user {user_id}.")
        await message.reply("Lambar wayar da ka tura ba daidai ba ce. Don Allah a gwada wata lambar.")
        await state.clear()
        if client.is_connected(): await client.disconnect()
        # Clean up partial session file if created
        if os.path.exists(client_session_path + '.session'):
            os.remove(client_session_path + '.session')
    except FloodWaitError as e:
        logger.error(f"Flood wait for {phone_number} from user {user_id}: {e}")
        await message.reply(f"An yi ƙoƙarin shiga da yawa daga wannan lambar ko IP. Don Allah a gwada bayan mintuna {e.seconds/60:.0f} kadan.")
        await state.clear()
        if client.is_connected(): await client.disconnect()
        if os.path.exists(client_session_path + '.session'):
            os.remove(client_session_path + '.session')
    except Exception as e:
        logger.error(f"Error sending code for {phone_number} to user {user_id}: {e}", exc_info=True)
        await message.reply("Wani kuskure ya faru yayin aika lambar sirri. Don Allah a gwada wata lambar ko kuma daga baya.")
        await state.clear()
        if client.is_connected(): await client.disconnect()
        if os.path.exists(client_session_path + '.session'):
            os.remove(client_session_path + '.session')

@dp.message(SellAccountStates.waiting_for_otp)
async def process_otp(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    otp_code = message.text.strip()
    data = await state.get_data()
    current_phone = data.get('current_phone')
    client = data.get('telethon_client')
    client_session_path = data.get('client_session_path')

    if not current_phone or not client or not client_session_path:
        logger.error(f"OTP state entered without phone/client/session_path for user {user_id}.")
        await message.reply("Wani kuskure ya faru. Don Allah a sake farawa da /start.")
        await state.clear()
        if client and client.is_connected(): await client.disconnect()
        return

    try:
        await client.sign_in(current_phone, otp_code)
        # If sign-in is successful, it means no 2FA or 2FA was already handled (unlikely here)
        logger.info(f"Successfully logged in {current_phone} for user {user_id}.")

        await update_account_status(current_phone, 'ready_for_payment')
        await add_number_to_cooldown(current_phone) # Add/update cooldown after successful login

        await message.reply(
            "An shiga account din ku cikin nasara ku cire shi daga na'urar ku. "
            "Za a biya ku bisa ga adadin account din da kuka kawo. "
            "Ana biyan kuɗi daga karfe 8:00 na dare (WAT) zuwa gaba. Don Allah ka shirya tura bukatar biya.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear() # Clear state after successful login

    except PhoneCodeInvalidError:
        logger.warning(f"Invalid OTP {otp_code} for {current_phone} by user {user_id}.")
        await message.reply("Lambar sirrin da ka tura ba daidai ba ce. Don Allah a sake gwadawa.")
    except SessionPasswordNeededError:
        logger.warning(f"2FA detected for {current_phone} for user {user_id}.")
        await message.reply(
            "An gano Two-Factor Authentication (2FA) akan wannan account! "
            "Don Allah ka tura lambar sirrin 2FA dinka domin kammala shiga."
        )
        await update_account_status(current_phone, 'pending_2fa') # Update status to pending 2FA
        await state.set_state(SellAccountStates.waiting_for_2fa)
    except FloodWaitError as e:
        logger.error(f"Flood wait for {current_phone} during OTP from user {user_id}: {e}")
        await message.reply(f"An yi ƙoƙarin shiga da yawa. Don Allah a gwada bayan mintuna {e.seconds/60:.0f} kadan.")
        await state.clear()
        if client.is_connected(): await client.disconnect()
        if os.path.exists(client_session_path + '.session'):
            os.remove(client_session_path + '.session') # Remove partial session on flood wait
    except Exception as e:
        logger.error(f"Error processing OTP for {current_phone} by user {user_id}: {e}", exc_info=True)
        await message.reply("Wani kuskure ya faru yayin shiga. Don Allah a sake gwadawa daga farko da /start.")
        await state.clear()
        if client.is_connected(): await client.disconnect()
        if os.path.exists(client_session_path + '.session'):
            os.remove(client_session_path + '.session') # Remove session on general error
    finally:
        # Disconnect only if not going to 2FA state, otherwise client is needed
        if await state.get_state() != SellAccountStates.waiting_for_2fa and client.is_connected():
            await client.disconnect()

@dp.message(SellAccountStates.waiting_for_2fa)
async def process_2fa(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    password_2fa = message.text.strip()
    data = await state.get_data()
    current_phone = data.get('current_phone')
    client = data.get('telethon_client')
    client_session_path = data.get('client_session_path')

    if not current_phone or not client or not client_session_path:
        logger.error(f"2FA state entered without phone/client/session_path for user {user_id}.")
        await message.reply("Wani kuskure ya faru. Don Allah a sake farawa da /start.")
        await state.clear()
        if client and client.is_connected(): await client.disconnect()
        return

    try:
        await client.sign_in(password=password_2fa)
        logger.info(f"Successfully logged in {current_phone} with 2FA for user {user_id}.")

        await update_account_status(current_phone, 'ready_for_payment')
        await add_number_to_cooldown(current_phone) # Add/update cooldown after successful login

        await message.reply(
            "An shiga account din ku cikin nasara ku cire shi daga na'urar ku. "
            "Z
