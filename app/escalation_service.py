"""
escalation_service.py
Creates escalation queue records for human review.
Triggered by distress, RG, fraud signals, or low confidence.
"""

import uuid
from datetime import datetime, timezone
from app.db_init import get_connection


def create(
    session_id: str,
    user_id:    str | None,
    message:    str,
    reason:     str,
    risk_level: str,
) -> str:
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO escalation_queue
               (ticket_id, user_id, message, reason, risk_level, status, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (
                ticket_id,
                user_id or "anonymous",
                message[:500],
                reason,
                risk_level,
                "open",
                datetime.now(timezone.utc).isoformat(),
            )
        )
        conn.commit()
    except Exception as e:
        print(f"[escalation_service] Warning: {e}")
    finally:
        conn.close()
    return ticket_id
