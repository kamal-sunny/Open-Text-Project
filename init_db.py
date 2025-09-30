import sqlite3
from datetime import datetime

conn = sqlite3.connect("game.db")
cur = conn.cursor()

# ---------- Users Table ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    reg_date TEXT NOT NULL,
    win_status TEXT,
    last_login TEXT
)
""")

# ---------- Words Table ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE NOT NULL,
    added_by TEXT NOT NULL
)
""")

# ---------- User Guesses Table ----------
cur.execute("""
CREATE TABLE IF NOT EXISTS user_guesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    word TEXT NOT NULL,
    guesses INTEGER NOT NULL,
    correct INTEGER NOT NULL,
    date TEXT NOT NULL
)
""")

# ---------- Insert Default Admin ----------
cur.execute("SELECT * FROM users WHERE role='ADMIN'")
admin = cur.fetchone()
if not admin:
    cur.execute("""
    INSERT INTO users (username, password, role, reg_date, win_status) 
    VALUES (?, ?, ?, ?, ?)
    """, ("admin", "admin123", "ADMIN", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "N/A"))

# ---------- Insert Sample Player ----------
cur.execute("""
INSERT OR IGNORE INTO users (username, password, role, reg_date, win_status)
VALUES (?, ?, ?, ?, ?)
""", ("player1", "pass1", "PLAYER", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "No"))

# ---------- Insert Sample Words ----------
words = [
    "APPLE", "MANGO", "BRAIN", "TRAIN", "SCORE",
    "PLANT", "MUSIC", "LIGHT", "STARS", "CLOUD",
    "WATER", "EARTH", "HAPPY", "SMILE", "CODES",
    "GAMES", "LEVEL", "POWER", "MAGIC", "HEART"
]

for w in words:
    cur.execute("INSERT OR IGNORE INTO words (word, added_by) VALUES (?, ?)", (w, "admin"))

conn.commit()
conn.close()

print("✅ Database initialized with admin, sample player, 20 words & user_guesses table")
