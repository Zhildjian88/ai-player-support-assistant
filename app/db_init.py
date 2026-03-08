"""
db_init.py
Initialises the SQLite database and seeds runtime tables from JSON files.
Run once on first setup: python -m app.db_init
"""

import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "app.db"
DATA_DIR = Path(__file__).parent.parent / "data"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── Users table (seeded from users.json) ─────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            email TEXT,
            country TEXT,
            kyc_status TEXT,
            account_status TEXT,
            vip_tier TEXT,
            rg_flag INTEGER DEFAULT 0,
            deposit_limit_daily REAL,
            deposit_limit_weekly REAL,
            deposit_limit_monthly REAL,
            self_excluded INTEGER DEFAULT 0,
            cooling_off_until TEXT,
            registered_date TEXT,
            last_login TEXT,
            preferred_language TEXT DEFAULT 'en'
        )
    """)

    # ── Payments table (seeded from payments.json) ────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id TEXT,
            type TEXT,
            method TEXT,
            status TEXT,
            amount REAL,
            currency TEXT,
            created_at TEXT,
            updated_at TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # ── Promotions table (seeded from promotions.json) ────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS promotions (
            promotion_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            type TEXT,
            bonus_percent REAL,
            max_bonus REAL,
            min_deposit REAL,
            wagering_requirement REAL,
            start_date TEXT,
            end_date TEXT,
            segment TEXT,
            active INTEGER DEFAULT 1,
            terms TEXT,
            country_eligibility TEXT,
            valid_games TEXT
        )
    """)

    # ── Cache table (populated at runtime) ───────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_hash TEXT UNIQUE,
            question_normalised TEXT,
            answer TEXT,
            source TEXT,
            hit_count INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_accessed TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Audit log table (populated at runtime) ────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id TEXT,
            message TEXT,
            policy_result TEXT,
            distress_signal INTEGER DEFAULT 0,
            rg_signal INTEGER DEFAULT 0,
            fraud_signal INTEGER DEFAULT 0,
            route_taken TEXT,
            data_source TEXT,
            llm_called INTEGER DEFAULT 0,
            escalated INTEGER DEFAULT 0,
            risk_level TEXT DEFAULT 'LOW',
            response_preview TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Escalation queue (populated at runtime) ───────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS escalation_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT UNIQUE,
            user_id TEXT,
            message TEXT,
            reason TEXT,
            risk_level TEXT,
            status TEXT DEFAULT 'open',
            assigned_to TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT
        )
    """)

    # ── LLM cost log (populated at runtime) ──────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS llm_cost_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            estimated_cost_usd REAL,
            llm_success INTEGER DEFAULT 1,
            latency_ms INTEGER,
            route TEXT DEFAULT 'llm_fallback',
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Conversation context (bounded session window) ─────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversation_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            turn_index INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_context_session
        ON conversation_context(session_id, turn_index)
    """)

    conn.commit()
    print("[db_init] Schema created.")

    # ── Seed tables from JSON ─────────────────────────────────────────────────
    _seed_users(conn)
    _seed_payments(conn)
    _seed_promotions(conn)

    conn.close()
    print("[db_init] Database initialised at:", DB_PATH)


def _seed_users(conn):
    with open(DATA_DIR / "users.json") as f:
        users = json.load(f)
    c = conn.cursor()
    for u in users:
        c.execute("""
            INSERT OR IGNORE INTO users VALUES (
                :user_id, :username, :email, :country,
                :kyc_status, :account_status, :vip_tier, :rg_flag,
                :deposit_limit_daily, :deposit_limit_weekly, :deposit_limit_monthly,
                :self_excluded, :cooling_off_until, :registered_date, :last_login,
                :preferred_language
            )
        """, u)
    conn.commit()
    print(f"[db_init] Seeded {len(users)} users.")


def _seed_payments(conn):
    with open(DATA_DIR / "payments.json") as f:
        payments = json.load(f)
    c = conn.cursor()
    for p in payments:
        c.execute("""
            INSERT OR IGNORE INTO payments VALUES (
                :payment_id, :user_id, :type, :method, :status,
                :amount, :currency, :created_at, :updated_at, :notes
            )
        """, p)
    conn.commit()
    print(f"[db_init] Seeded {len(payments)} payments.")


def _seed_promotions(conn):
    with open(DATA_DIR / "promotions.json") as f:
        promos = json.load(f)
    c = conn.cursor()
    for p in promos:
        c.execute("""
            INSERT OR IGNORE INTO promotions VALUES (
                :promotion_id, :title, :description, :type,
                :bonus_percent, :max_bonus, :min_deposit, :wagering_requirement,
                :start_date, :end_date, :segment, :active, :terms,
                :country_eligibility, :valid_games
            )
        """, {
            "promotion_id": p["promotion_id"],
            "title": p["title"],
            "description": p["description"],
            "type": p["type"],
            "bonus_percent": p.get("bonus_percent"),
            "max_bonus": p.get("max_bonus"),
            "min_deposit": p.get("min_deposit"),
            "wagering_requirement": p.get("wagering_requirement"),
            "start_date": p["start_date"],
            "end_date": p["end_date"],
            "segment": json.dumps(p.get("segment", "")),
            "active": 1 if p["active"] else 0,
            "terms": p["terms"],
            "country_eligibility": json.dumps(p.get("country_eligibility", [])),
            "valid_games": json.dumps(p.get("valid_games", []))
        })
    conn.commit()
    print(f"[db_init] Seeded {len(promos)} promotions.")


if __name__ == "__main__":
    init_db()
