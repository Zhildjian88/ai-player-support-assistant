"""
fraud_detector.py
Detects fraud and security signals — unauthorised account access,
suspicious login activity, unrecognised transactions, identity theft.

Sources:
  - Fingerprint.com: Online Gambling Fraud Prevention
  - UKGC / MGA fraud typologies
  - Common player-reported security incidents

When triggered: risk_level = HIGH, escalate for security review.
"""

# ── Unauthorised account access ───────────────────────────────────────────────
UNAUTHORISED_ACCESS = [
    "someone logged in", "someone else logged in",
    "logged in from another country", "login from another country",
    "unauthorised access", "unauthorized access",
    "account hacked", "account was hacked", "account has been hacked",
    "my account was compromised", "account compromised",
    "someone accessed my account", "someone else using my account",
    "someone got into my account", "someone is in my account",
    "login from unknown location", "login from unknown device",
    "login alert", "suspicious login", "unrecognised login",
    "unrecognized login", "strange login",
    "password changed without", "password was changed without",
    "email changed without", "details changed without",
    "someone changed my password", "someone changed my email",
]

# ── Unrecognised transactions ─────────────────────────────────────────────────
UNRECOGNISED_TRANSACTIONS = [
    "did not make this withdrawal", "did not make this deposit",
    "did not authorise", "did not authorize",
    "did not request this", "i did not request this",
    "unrecognised transaction", "unrecognized transaction",
    "unrecognised charge", "unrecognized charge",
    "money missing from account", "money missing",
    "balance is wrong", "balance incorrect",
    "funds missing", "missing funds",
    "transaction i don't recognise", "transaction i don't recognize",
    "withdrawal i didn't make", "deposit i didn't make",
]

# ── Payment fraud & identity theft ───────────────────────────────────────────
PAYMENT_FRAUD = [
    "someone used my card", "my card was used",
    "card used without permission", "card used without my knowledge",
    "stolen card", "my card was stolen",
    "i was phished", "phishing", "phishing email", "phishing link",
    "clicked a fake link", "gave my details to a fake site",
    "identity stolen", "identity theft", "someone stole my identity",
    "someone is using my identity",
]

# ── Suspicious activity (general) ─────────────────────────────────────────────
SUSPICIOUS_ACTIVITY = [
    "suspicious activity", "suspicious transaction",
    "account acting strange", "account behaving strangely",
    "i think i was scammed", "i think i've been scammed",
    "someone is impersonating me",
    "fake account in my name",
    # Disputed / missing funds
    "balance is zero", "balance shows zero",
    "where is my money", "where did my money go",
    "did not withdraw", "i did not withdraw",
    "unknown bank account", "unrecognised bank account", "unrecognized bank account",
    "stolen credit card", "stolen debit card",
    "scam withdrawal", "fraudulent withdrawal",
    "missing chips", "chips are missing", "chips gone",
    "fake bet", "bet i didn't place", "bet i did not place",
    "transaction i never made",
]

FRAUD_KEYWORDS = (
    UNAUTHORISED_ACCESS
    + UNRECOGNISED_TRANSACTIONS
    + PAYMENT_FRAUD
    + SUSPICIOUS_ACTIVITY
)

SAFE_RESPONSE = (
    "Thank you for reporting this. We take account security very seriously.\n\n"
    "Please take these steps immediately:\n"
    "1. Change your password using the Forgot Password link\n"
    "2. Enable two-factor authentication in your Security Settings\n"
    "3. Do not share your login details with anyone\n\n"
    "I have flagged your account for an urgent security review. "
    "Our security team will investigate recent login activity and contact you. "
    "If you believe a transaction was made without your authorisation, "
    "please contact us via live chat with the payment details."
)


def check(message: str) -> dict:
    normalised = message.lower()
    for keyword in FRAUD_KEYWORDS:
        if keyword in normalised:
            return {"signal": True, "response": SAFE_RESPONSE}
    return {"signal": False, "response": ""}
