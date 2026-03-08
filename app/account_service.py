"""
account_service.py
Looks up real account and KYC status from SQLite.
"""

ACCOUNT_TRIGGERS = [
    "account status", "account locked", "account blocked", "account suspended",
    "account restricted", "kyc", "verification status", "verify my account",
    "my account", "account access", "vip", "vip tier",
    "deposit limit", "my limit", "self exclusion status",
]


def lookup(message: str, user_id: str) -> dict:
    from app.db_init import get_connection
    normalised = message.lower()

    if not any(t in normalised for t in ACCOUNT_TRIGGERS):
        return {"matched": False, "response": ""}

    conn = get_connection()
    row  = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()

    if not row:
        return {"matched": False, "response": ""}

    user = dict(row)
    acct = user["account_status"]
    kyc  = user["kyc_status"]
    vip  = user["vip_tier"].title()

    if "kyc" in normalised or "verif" in normalised:
        status_map = {
            "verified":  "Your identity has been successfully verified. You have full access to all features.",
            "pending":   "Your identity verification is currently under review. This typically takes 24–48 hours.",
            "rejected":  "Your identity verification was not approved. Please resubmit clear, current documents.",
        }
        response = status_map.get(kyc, f"Your KYC status is: {kyc}. Please contact support for details.")

    elif "vip" in normalised:
        response = f"Your current VIP tier is {vip}."

    elif "limit" in normalised:
        response = (
            f"Your current deposit limits are: "
            f"Daily {user['deposit_limit_daily']:,.0f} | "
            f"Weekly {user['deposit_limit_weekly']:,.0f} | "
            f"Monthly {user['deposit_limit_monthly']:,.0f}. "
            "You can adjust these in your Responsible Gaming settings."
        )

    else:
        acct_map = {
            "active":        "Your account is active and in good standing.",
            "restricted":    "Your account is currently restricted. Please contact support to resolve this.",
            "suspended":     "Your account has been suspended. Please contact our support team for assistance.",
            "self_excluded": "Your account is self-excluded. If you believe this was in error, please contact support.",
        }
        response = acct_map.get(acct, f"Your account status is: {acct}. Please contact support.")

    return {"matched": True, "response": response}
