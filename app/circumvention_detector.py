"""
circumvention_detector.py
Detects attempts to bypass self-imposed or operator-imposed controls —
limit removal, exclusion circumvention, multi-accounting, VPN use to
re-access a blocked account.

Sources:
  - Fingerprint.com: Online Gambling Fraud Prevention (gnoming, multi-accounting)
  - UKGC enforcement cases: self-exclusion breach typologies
  - GamCare: patterns of players attempting to circumvent cooling-off periods
  - Internet Responsible Gambling Standards (NCPG, Dec 2023)

When triggered: risk_level = HIGH, flag for manual Risk team review.
Dual purpose: player welfare (circumventing their own limits) and
fraud prevention (gnoming / duplicate accounts).
"""

# ── Limit removal requests ────────────────────────────────────────────────────
# Player asking to remove or raise controls they previously set.
# Requires mandatory cool-off period before action under UKGC / MGA rules.
LIMIT_REMOVAL = [
    "remove my deposit limit", "remove my limit",
    "increase my deposit limit", "increase my limit",
    "raise my limit", "raise my deposit limit",
    "lift my limit", "lift my deposit limit",
    "cancel my deposit limit", "cancel my limit",
    "remove my loss limit", "remove my spending limit",
    "increase my loss limit", "increase my spending limit",
    "remove my session limit", "remove my time limit",
    "increase my session limit", "increase my time limit",
    "override my limit",
]

# ── Self-exclusion / cooling-off circumvention ────────────────────────────────
# Requests to undo a self-exclusion or cooling-off before its expiry.
# These must be flagged — operators are legally prohibited from acting
# immediately on such requests (mandatory 24-hour / 7-day cooling-off).
EXCLUSION_CIRCUMVENTION = [
    "remove my self exclusion", "remove my self-exclusion",
    "cancel my self exclusion", "cancel my self-exclusion",
    "end my self exclusion", "end my self-exclusion",
    "reverse my self exclusion", "undo my self exclusion",
    "lift my exclusion", "remove exclusion",
    "i want to play again", "i want to gamble again",
    "let me back in", "reopen my account",
    "remove my cooling off", "cancel my cooling off",
    "end my cooling off", "reverse my cooling off",
    "i'm ready to play again", "i changed my mind about excluding",
]

# ── Multi-accounting / gnoming ────────────────────────────────────────────────
# Signals suggesting creation of duplicate accounts to bypass controls
# or claim multiple bonuses. (Source: Fingerprint.com fraud typologies)
MULTI_ACCOUNTING = [
    "new account", "create another account", "open another account",
    "make a new account", "register a new account",
    "different email", "use a different email",
    "different name", "use a different name",
    "second account", "another account",
    "my other account", "my second account",
    "bypass the ban", "get around the ban",
    "get around the block", "bypass the block",
    "create a new profile", "new profile",
]

# ── VPN / IP circumvention ────────────────────────────────────────────────────
# Using VPN to access a geo-blocked or suspended account.
VPN_CIRCUMVENTION = [
    "use a vpn", "using a vpn", "vpn to access",
    "vpn to play", "vpn to get around",
    "change my ip", "change my location",
    "why am i blocked", "why is my account blocked",
    "why can't i access", "why am i restricted",
    "access from another country",
]

# ── Workarounds (general) ─────────────────────────────────────────────────────
GENERAL_BYPASS = [
    "bypass", "workaround", "get around my limit",
    "get around my restriction", "get around the system",
    "find a way around", "loophole",
    "still play even though excluded",
    "gamble while excluded", "play while excluded",
    "gamble with a family member's account",
    "use someone else's account",
]

CIRCUMVENTION_KEYWORDS = (
    LIMIT_REMOVAL
    + EXCLUSION_CIRCUMVENTION
    + MULTI_ACCOUNTING
    + VPN_CIRCUMVENTION
    + GENERAL_BYPASS
)

# Response differentiates between two sub-cases:
# 1. Limit/exclusion removal (welfare — explain the cooling-off requirement)
# 2. Multi-account / VPN (fraud — flag for Risk team)

WELFARE_RESPONSE = (
    "Thank you for reaching out. We take responsible gaming very seriously "
    "and have rules in place to protect players.\n\n"
    "If you set a deposit limit or cooling-off period, there is a mandatory "
    "waiting period before any changes can take effect — this is required by "
    "our licensing regulations to ensure player welfare.\n\n"
    "If you requested a self-exclusion, this cannot be reversed until the "
    "exclusion period has ended. This is a firm safeguard designed to protect you.\n\n"
    "A member of our player welfare team will review your request and contact "
    "you with more information."
)

FRAUD_RESPONSE = (
    "Thank you for contacting us. For account access and restriction queries, "
    "please verify your identity via our secure verification process.\n\n"
    "Please note that creating multiple accounts or using technical means to "
    "bypass account restrictions is a violation of our Terms of Service "
    "and may result in permanent account closure.\n\n"
    "I have flagged this query for review by our Risk and Compliance team."
)

_WELFARE_SIGNALS = set(LIMIT_REMOVAL + EXCLUSION_CIRCUMVENTION)
_FRAUD_SIGNALS = set(MULTI_ACCOUNTING + VPN_CIRCUMVENTION + GENERAL_BYPASS)


def check(message: str) -> dict:
    """
    Returns {"signal": bool, "subtype": str, "response": str}
    subtype: "welfare" | "fraud" | None
    """
    normalised = message.lower()
    for keyword in CIRCUMVENTION_KEYWORDS:
        if keyword in normalised:
            if keyword in _WELFARE_SIGNALS:
                return {"signal": True, "subtype": "welfare",
                        "response": WELFARE_RESPONSE}
            else:
                return {"signal": True, "subtype": "fraud",
                        "response": FRAUD_RESPONSE}
    return {"signal": False, "subtype": None, "response": ""}
