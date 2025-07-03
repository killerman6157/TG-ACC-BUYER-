# login_with_session.py
import asyncio
from telethon.sync import TelegramClient
import os
from dotenv import load_dotenv

# Load environment variables (API_ID, API_HASH) from your .env file
load_dotenv() 

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')

async def login_with_session(session_file_path):
    # Extract session name from the full path. Telethon expects just the name.
    # Example: 'path/to/sessions/2348167757987.session' -> 'path/to/sessions/2348167757987'
    session_name_without_extension = os.path.splitext(session_file_path)[0]

    # Initialize TelegramClient with the session name
    client = TelegramClient(session_name_without_extension, API_ID, API_HASH)

    try:
        print(f"Connecting to Telegram with session: {session_file_path}...")
        await client.connect()

        if not await client.is_user_authorized():
            print(f"Error: Session '{session_file_path}' is not authorized. It might be corrupted or logged out. Please try getting a fresh account.")
            return False

        me = await client.get_me()
        print(f"Successfully logged in as: {me.first_name} {me.last_name if me.last_name else ''} (@{me.username})")
        print(f"Phone Number: {me.phone}")

        # --- IMPORTANT: Guide for Setting 2FA ---
        print("\n--- MATAKI NA GABA: SAITA 2FA A WANNAN ACCOUNT ---")
        print("1. Da farko, a wayarka/kwamfutarka, ka shiga Telegram app (ko Telegram Desktop).")
        print("2. Yi kokarin shiga wannan account din ta amfani da lambar wayar.")
        print("3. Idan ya nemi OTP, zai yiwu bot din ya riga ya shiga, don haka zai nemi 2FA passcode.")
        print("4. Idan har ka iya shiga account din a Telegram app dinka, nan take ka je Settings > Privacy and Security > Two-Step Verification (ko Two-Factor Authentication).")
        print("5. Sa'annan ka saita sabon Two-Factor Authentication passcode wanda kai kadai ka sani. Wannan yana da matukar muhimmanci don amincin account din.")
        print("6. Bayan ka saita 2FA, zaka iya cire account din daga duk wata na'ura da aka shiga da shi (ban da naka).")
        print("\n-----------------------------------------------------")

        # This client stays connected after login. You can perform actions or just disconnect.
        # For now, we'll keep it connected until manually stopped.
        print("Client is now connected. Press Ctrl+C to disconnect and exit.")
        while True:
            await asyncio.sleep(1) # Keep the script running

    except Exception as e:
        print(f"Error logging in with session {session_file_path}: {e}")
        return False
    finally:
        if client.is_connected():
            await client.disconnect()
            print(f"Disconnected from Telegram for session: {session_file_path}")

if __name__ == "__main__":
    # Ensure API_ID and API_HASH are loaded
    if not API_ID or not API_HASH:
        print("ERROR: API_ID or API_HASH not found in .env. Please configure it.")
        exit(1)

    session_file = input("Shigar da cikakken hanyar zuwa session file (misali: sessions/2348167757987.session): ")
    if not os.path.exists(session_file):
        print(f"Fayil '{session_file}' bai wanzu ba. Tabbatar hanyar daidai ce.")
    else:
        asyncio.run(login_with_session(session_file))


