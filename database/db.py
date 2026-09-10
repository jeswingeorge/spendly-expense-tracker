import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

# ---- Configuration ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, "expense_tracker.db")

# Fixed category list used by seed data (and, later, expense forms)
CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


# ---- Connection ----
def get_db():
    """Open a new SQLite connection with dict-like rows and FK enforcement on.

    PRAGMA foreign_keys is per-connection, not persisted in the DB file, so
    always go through this function rather than calling sqlite3.connect()
    directly elsewhere.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---- Schema ----
def init_db(db=None):
    """Create the users and expenses tables if they don't already exist.

    Safe to call multiple times. Pass an existing connection via `db` to
    reuse it (e.g. in tests); otherwise a connection is opened and closed
    internally.
    """
    conn = db or get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    if db is None:
        conn.close()


# ---- Seed Data ----
def seed_db(db=None):
    """Insert a demo user and sample expenses, but only on a fresh database.

    Idempotent: if the users table already has rows, this is a no-op.
    """
    conn = db or get_db()

    existing = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    if existing["count"] > 0:
        if db is None:
            conn.close()
        return

    password_hash = generate_password_hash("demo123")
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cursor.lastrowid

    today = date.today()

    def spend_date(day):
        return f"{today.year:04d}-{today.month:02d}-{day:02d}"

    # 8 sample expenses covering all fixed categories, spread across the
    # current month. Days are kept <= 28 so this is valid in every month.
    sample_expenses = [
        (user_id, 450.00, "Food", spend_date(2), "Groceries at BigBasket"),
        (user_id, 120.00, "Transport", spend_date(4), "Auto fare to office"),
        (user_id, 1499.00, "Bills", spend_date(5), "Electricity bill"),
        (user_id, 850.00, "Health", spend_date(8), "Pharmacy purchase"),
        (user_id, 600.00, "Entertainment", spend_date(11), "Movie tickets"),
        (user_id, 2200.00, "Shopping", spend_date(14), "New shoes"),
        (user_id, 300.00, "Other", spend_date(17), "Miscellaneous"),
        (user_id, 250.00, "Food", spend_date(20), "Lunch with friends"),
    ]
    conn.executemany(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        sample_expenses,
    )

    conn.commit()
    if db is None:
        conn.close()


# ---- Users ----
def get_user_by_email(email, db=None):
    """Return the users row matching `email`, or None if there is no match.

    Pass an existing connection via `db` to reuse it (e.g. in tests);
    otherwise a connection is opened and closed internally.
    """
    conn = db or get_db()

    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

    if db is None:
        conn.close()
    return row


def get_user_by_id(user_id, db=None):
    """Return the users row matching `user_id`, or None if there is no match.

    Pass an existing connection via `db` to reuse it (e.g. in tests);
    otherwise a connection is opened and closed internally.
    """
    conn = db or get_db()

    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    if db is None:
        conn.close()
    return row


def create_user(name, email, password, db=None):
    """Hash `password`, insert a new users row, and return its id.

    Raises sqlite3.IntegrityError if `email` is already registered (the
    UNIQUE constraint on users.email). Pass an existing connection via `db`
    to reuse it; otherwise a connection is opened and closed internally.
    """
    conn = db or get_db()

    password_hash = generate_password_hash(password)
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        if db is None:
            conn.close()
