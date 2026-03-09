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


def lookup(message: str) -> dict:
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
