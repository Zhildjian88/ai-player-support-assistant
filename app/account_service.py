"""
account_service.py
Looks up real account and KYC status from SQLite.
"""

ACCOUNT_TRIGGERS = [
    "my balance", "account balance", "check balance", "wallet balance",
    "account status", "account locked", "account blocked", "account suspended",
    "account restricted", "my kyc", "kyc status", "my verification",
    "verification status", "verify my account", "my account status",
    "account access", "my vip", "vip tier", "my vip tier",
    "deposit limit", "my limit", "self exclusion status",
]

# General questions about what something IS — route to FAQ/LLM instead
ACCOUNT_EXCLUSIONS = [
    "what is kyc", "what is a kyc", "what does kyc mean",
    "what is kyc?", "tell me about kyc", "explain kyc",
    "more about kyc", "what is verification", "why do i need kyc",
    "how does kyc work", "what is vip", "how does vip work",
    "what is a deposit limit", "what are deposit limits",
    "what is self exclusion", "what is responsible gaming",
    "how do i set a deposit limit", "how do i set a limit",
    "how do i change my limit", "how do i reduce my limit",
    "how do i set a session limit", "how do i set a time limit",
    "how do i self exclude", "how do i take a break",
    "how do i close my account", "how do i reset my password",
    "how do i update my", "how do i change my",
]


def lookup(message: str, user_id: str) -> dict:
    from app.db_init import get_connection
    normalised = message.lower()

    if any(e in normalised for e in ACCOUNT_EXCLUSIONS):
        return {"matched": False, "response": ""}
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

    if any(b in normalised for b in ["balance", "wallet"]):
        acct_status = acct
        balance_msg = {
            "active":        "Your account is active. Your current balance is displayed in your account dashboard.",
            "restricted":    "Your account is currently restricted. Please contact support — balance withdrawals may be affected.",
            "suspended":     "Your account is suspended. Please contact support to access your balance.",
            "self_excluded": "Your account is self-excluded. Please contact support regarding your balance.",
        }
        response = balance_msg.get(acct_status, "Your balance is available in your account dashboard.")

    elif "kyc" in normalised or "verif" in normalised:
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
