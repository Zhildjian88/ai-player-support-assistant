"""
payment_service.py
Looks up real payment/withdrawal/deposit status from SQLite.
Never invents status values — all data comes from the database.
"""

PAYMENT_TRIGGERS = [
    "withdrawal", "withdraw", "payout", "cashout", "cash out",
    "deposit", "transaction", "payment status", "transfer",
    "pending payment", "my money",
]


def lookup(message: str, user_id: str) -> dict:
    from app.db_init import get_connection
    normalised = message.lower()

    if not any(t in normalised for t in PAYMENT_TRIGGERS):
        return {"matched": False, "response": ""}

    conn   = get_connection()
    rows   = conn.execute(
        """SELECT * FROM payments WHERE user_id = ?
           ORDER BY updated_at DESC LIMIT 5""",
        (user_id,)
    ).fetchall()
    conn.close()

    if not rows:
        return {"matched": False, "response": ""}

    payments = [dict(r) for r in rows]

    # Filter to most relevant based on message keywords
    if any(w in normalised for w in ["withdrawal", "withdraw", "payout", "cashout"]):
        relevant = [p for p in payments if p["type"] == "withdrawal"]
    elif any(w in normalised for w in ["deposit", "top up", "topup", "add funds"]):
        relevant = [p for p in payments if p["type"] == "deposit"]
    else:
        relevant = payments

    if not relevant:
        relevant = payments

    latest  = relevant[0]
    status  = latest["status"].upper()
    amount  = latest["amount"]
    ccy     = latest["currency"]
    method  = latest["method"].replace("_", " ").title()
    notes   = latest["notes"] or ""
    ptype   = latest["type"].title()

    status_messages = {
        "PENDING":    f"Your {ptype.lower()} of {ccy} {amount:,.0f} via {method} is currently pending. {notes}",
        "PROCESSING": f"Your {ptype.lower()} of {ccy} {amount:,.0f} via {method} is being processed. {notes}",
        "COMPLETED":  f"Your {ptype.lower()} of {ccy} {amount:,.0f} via {method} has been completed successfully.",
        "REJECTED":   f"Your {ptype.lower()} of {ccy} {amount:,.0f} via {method} was not processed. Reason: {notes}",
        "BLOCKED":    f"Your {ptype.lower()} of {ccy} {amount:,.0f} via {method} has been blocked. Reason: {notes}",
        "FAILED":     f"Your {ptype.lower()} of {ccy} {amount:,.0f} via {method} failed. {notes} Please try again or contact support.",
    }

    response = status_messages.get(
        status,
        f"Your {ptype.lower()} of {ccy} {amount:,.0f} has status: {status}. Please contact support for details."
    )

    return {"matched": True, "response": response}
