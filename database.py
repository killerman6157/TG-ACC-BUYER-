# ✅ FILE: database.py
import sqlite3

def init_db():
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            verified_accounts INTEGER DEFAULT 0,
            unverified_accounts INTEGER DEFAULT 0,
            balance REAL DEFAULT 0,
            language TEXT DEFAULT 'en'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            number TEXT,
            verified INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()
    if not data:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        data = cursor.fetchone()
    conn.close()
    return data

def update_language(user_id, lang):
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def log_submission(user_id, number, verified):
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO submissions (user_id, number, verified) VALUES (?, ?, ?)", (user_id, number, verified))
    if verified:
        cursor.execute("UPDATE users SET verified_accounts = verified_accounts + 1, balance = balance + 0.3 WHERE user_id=?", (user_id,))
    else:
        cursor.execute("UPDATE users SET unverified_accounts = unverified_accounts + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("accounts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM submissions WHERE verified = 1")
    verified = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM submissions WHERE verified = 0")
    unverified = cursor.fetchone()[0]
    conn.close()
    return users, verified, unverified
