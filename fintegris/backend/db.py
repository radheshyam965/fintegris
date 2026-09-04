"""
Fintegris - SQLite database layer.

Kept deliberately simple (raw sqlite3, no ORM) so the whole backend
can run with zero external services -- perfect for a hackathon demo.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "fintegris.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    doc_type TEXT NOT NULL DEFAULT 'general',   -- general | bank_statement | company_books
    filepath TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',     -- uploaded | processed | error
    uploaded_at TEXT NOT NULL,
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id TEXT NOT NULL,
    date TEXT,
    vendor_raw TEXT,
    vendor TEXT,
    amount REAL,
    description TEXT,
    source_document TEXT,
    doc_type TEXT NOT NULL DEFAULT 'general',
    normalized INTEGER NOT NULL DEFAULT 0,
    duplicate_flag INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gl_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id TEXT NOT NULL,
    vendor TEXT,
    gl_code TEXT,
    gl_category TEXT,
    confidence REAL,
    reason TEXT,
    needs_review INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id TEXT NOT NULL,
    vendor TEXT,
    bank_amount REAL,
    books_amount REAL,
    difference REAL,
    status TEXT,          -- MATCHED | AMOUNT_MISMATCH | MISSING_IN_BANK | MISSING_IN_BOOKS
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id TEXT NOT NULL,
    reason TEXT,
    severity TEXT,        -- Low | Medium | High
    difference REAL,
    status TEXT NOT NULL DEFAULT 'Open',   -- Open | Resolved
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id TEXT NOT NULL,
    vendor TEXT,
    reason TEXT,
    ai_recommendation TEXT,
    bank_amount REAL,
    books_amount REAL,
    difference REAL,
    status TEXT NOT NULL DEFAULT 'Pending',   -- Pending | Approved | Rejected | Investigating
    decision_by TEXT,
    decision_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    result TEXT NOT NULL
);
"""


def init_db():
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def reset_db():
    """Wipe all transactional data but keep schema - handy between demo runs."""
    conn = get_conn()
    for t in ["transactions", "gl_mappings", "reconciliations", "anomalies", "reviews", "audit_log", "documents"]:
        conn.execute(f"DELETE FROM {t}")
    conn.commit()
    conn.close()


def log_audit(action: str, actor: str, result: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO audit_log (timestamp, action, actor, result) VALUES (?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, actor, result),
    )
    conn.commit()
    conn.close()
