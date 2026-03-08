"""
audit_logger.py
Records every routing decision to the audit_log table.
Provides full decision traceability for compliance and monitoring.
"""

from datetime import datetime, timezone
from app.db_init import get_connection


def log(
    session_id:      str,
    user_id:         str | None,
    message:         str,
    route_taken:     str,
    risk_level:      str,
    distress_signal: bool,
    rg_signal:       bool,
    fraud_signal:    bool,
    escalated:       bool,
    response:        str,
    llm_called:      bool = False,
    policy_result:   str  = "PASS",
):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO audit_log
               (session_id, user_id, message, policy_result, distress_signal,
                rg_signal, fraud_signal, route_taken, data_source, llm_called,
                escalated, risk_level, response_preview, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                session_id,
                user_id or "anonymous",
                message[:500],
                policy_result,
                1 if distress_signal else 0,
                1 if rg_signal       else 0,
                1 if fraud_signal    else 0,
                route_taken,
                route_taken,
                1 if llm_called      else 0,
                1 if escalated       else 0,
                risk_level,
                response[:200],
                datetime.now(timezone.utc).isoformat(),
            )
        )
        conn.commit()
    except Exception as e:
        print(f"[audit_logger] Warning: {e}")
    finally:
        conn.close()
