# Telegram Account Receiver Bot 🤖

Wannan bot ɗin yana taimakawa wajen karɓar sabbin asusun Telegram daga masu siyarwa. Ana amfani da OTP login ta hanyar **Telethon**, ana adana bayanai a cikin **SQLite**, kuma yana goyon bayan harsuna biyu: **Hausa** da **Turanci**.

## ⚙️ Features

- 🔑 OTP login ta Telethon
- ❌ `/cancel` don dakatar da aiki
- 📊 `/account_balance` don duba verified/unverified da kudin user
- 💸 `/withdraw` don karɓar wallet/account info
- 🌐 `/language` don zaɓar yare (Hausa ko English)
- 🛡️ `/admin` don admin ya ga stats
- 🗃️ SQLite database
- 📁 Configurable `.env` file

---

## 🚀 Amfani

1. Tura `.env` da bayanan:

BOT_TOKEN=... (daga BotFather) API_ID=...     (daga https://my.telegram.org) API_HASH=...   (daga https://my.telegram.org) ADMIN_ID=...   (Telegram user ID naka)

2. Sanya dependencies:

pip install -r requirements.txt

3. Fara bot:

python main.py

---

## 📂 Structure

telegram_account_bot/ │ ├── main.py ├── database.py ├── messages.py ├── .env ├── requirements.txt ├── handlers/ │   ├── otp_handler.py │   ├── cancel_handler.py │   ├── balance_handler.py │   ├── withdraw_handler.py │   ├── language_handler.py │   └── admin_handler.py

---

## 📘 Commands

| Command             | Description                        |
|---------------------|------------------------------------|
| `/start`            | Tura number, login by OTP         |
| `/cancel`           | Soke aiki                          |
| `/account_balance`  | Nuna balance + account info        |
| `/withdraw`         | Tura Opay ko USDT wallet info      |
| `/language`         | Canza harshen amfani               |
| `/admin`            | (Admin Only) Stats na bot ɗin      |

---

## ❗ DISCLAIMER

> **Wannan bot yana da nufin taimakawa saye da siyar da sabbin Telegram accounts. Ba ya goyon bayan aikata laifi ko amfani da asusun da aka sace ko karya doka.**
>
> **Developer ba ya ɗaukar alhakin duk wani amfani da ba bisa ka’ida ba. Kai ne kawai kake da alhakin amfani da bot ɗin.**
>
> Yin amfani da wannan bot na nufin ka amince da wannan sharadi.

---
