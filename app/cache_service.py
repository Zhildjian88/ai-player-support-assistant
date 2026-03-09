"""
cache_service.py
Exact-match answer cache stored in SQLite.
Normalises questions before hashing for better hit rate.
"""

import hashlib
import re
from datetime import datetime, timezone
from app.db_init import get_connection


def _normalise(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _hash(text: str) -> str:
    return hashlib.md5(_normalise(text).encode()).hexdigest()


# Patterns that must never be served from cache.
# If a message contains any of these, bypass cache entirely —
# it must be evaluated fresh by the security pipeline on every request.
CACHE_BYPASS_PATTERNS = [
    "system prompt", "ignore all", "ignore previous",
    "abaikan semua", "abaikan arahan",
    "ลืมคำสั่ง", "system prompt ของ",
    "忽略所有", "忽略之前", "系统提示",
    "konfirmasi detail kartu", "riwayat transaksi",
    "detail kartu", "card details", "full card",
    "audit keamanan", "security audit",
    "decode and follow", "base64",
]


def _is_bypass(message: str) -> bool:
    """Returns True if the message should bypass the cache entirely."""
    normalised = message.lower()
    return any(p in normalised for p in CACHE_BYPASS_PATTERNS)


def lookup(message: str) -> dict:
    # Never serve cached responses for security-sensitive messages
    if _is_bypass(message):
        return {"hit": False, "response": ""}

    conn = get_connection()
    row  = conn.execute(
        "SELECT answer, source FROM cache WHERE question_hash = ?",
        (_hash(message),)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE cache SET hit_count = hit_count + 1, last_accessed = ? WHERE question_hash = ?",
            (datetime.now(timezone.utc).isoformat(), _hash(message))
        )
        conn.commit()
        conn.close()
        return {"hit": True, "response": row["answer"], "source": row["source"]}
    conn.close()
    return {"hit": False, "response": ""}


def store(message: str, answer: str, source: str):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO cache
               (question_hash, question_normalised, answer, source, created_at, last_accessed)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (_hash(message), _normalise(message), answer, source,
             datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
