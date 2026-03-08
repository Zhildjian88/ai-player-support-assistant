"""
rg_detector.py
Detects responsible gaming signals — problem gambling, compulsion,
loss of control, harm to finances or relationships, tool requests.

Sources:
  - DSM-5 Gambling Disorder criteria: tolerance, withdrawal, loss of control,
    preoccupation, chasing, escapism, deception, bailout, jeopardised relationships
  - GamCare / GambleAware intervention taxonomy
  - Internet Responsible Gambling Standards (NCPG, Dec 2023)
  - Journal of Gambling Studies: online account-based harm indicators

When triggered: risk_level = HIGH, escalate with RG tool offer.
"""

# ── Loss of control & compulsion ──────────────────────────────────────────────
# DSM-5: "persistent unsuccessful efforts to control, cut back, or stop"
LOSS_OF_CONTROL = [
    "cannot stop gambling", "can't stop gambling", "cant stop gambling",
    "unable to stop gambling", "tried to stop gambling",
    "tried to quit gambling", "keep going back to gambling",
    "gambling again even though", "relapsed gambling",
    "hooked on gambling", "hooked on betting",
    "obsessed with gambling", "obsessed with betting",
    "one more go", "just one more bet", "just one more spin",
    "last bet", "last spin", "last hand",
    "can't resist gambling", "cannot resist gambling",
    "urge to gamble", "urge to bet", "craving to gamble",
    "can't help myself gambling",
]

# ── Preoccupation & time distortion ──────────────────────────────────────────
# DSM-5: "preoccupied with gambling" / academic: prolonged sessions
PREOCCUPATION = [
    "gambling all night", "betting all night", "been gambling for hours",
    "gambled all day", "gambling everyday", "gambling every day",
    "gambling all the time", "can't stop thinking about gambling",
    "lost track of time gambling", "lost track of time",
    "only thing i think about", "all i think about is gambling",
    "gambling instead of sleeping", "gambling instead of working",
    "missed work because of gambling", "late because of gambling",
]

# ── Chasing losses ────────────────────────────────────────────────────────────
# DSM-5: "often returns another day to get even" / chasing criterion
CHASING = [
    "chasing losses", "chasing my losses",
    "trying to win back", "win back what i lost",
    "get my money back", "get back my losses",
    "need to win back", "have to win it back",
    "keep depositing to recover", "depositing more to chase",
    "doubling up to recover", "increasing bets to recover",
]

# ── Gambling as escape ────────────────────────────────────────────────────────
# DSM-5: "gambles as a way of escaping problems or relieving dysphoric mood"
ESCAPISM = [
    "gamble to forget", "gambling to forget",
    "gamble to escape", "gambling to escape",
    "gamble when stressed", "gambling when stressed",
    "gamble when depressed", "gambling when depressed",
    "gambling to cope", "gamble to cope",
    "gambling helps me feel better", "only feel good when gambling",
    "gambling is the only thing that helps",
    "use gambling to deal with",
]

# ── Financial harm signals ────────────────────────────────────────────────────
# DSM-5: relying on others for financial bailout; spending beyond means
FINANCIAL_HARM = [
    "spending too much on gambling", "spend too much on gambling",
    "spending more than i should", "spent more than i can afford",
    "gambling money i need", "gambling my rent money",
    "gambling my bill money", "gambling my savings",
    "losing too much", "lost too much money gambling",
    "keep losing money", "losing more and more",
    "gambling with money i don't have",
    "asked family for money to gamble", "borrowed money for gambling",
    "need money to gamble", "need a deposit to keep going",
    "begging for bonus", "please give me a bonus to continue",
]

# ── Irritability & withdrawal ─────────────────────────────────────────────────
# DSM-5: "restless or irritable when attempting to cut down or stop"
# Academic: aggressive CS communication as withdrawal signal
WITHDRAWAL = [
    "irritable when i don't gamble", "restless when i can't gamble",
    "anxious when i can't bet", "moody when i can't gamble",
    "need to gamble to feel normal", "feel terrible when not gambling",
]

# ── Deception & secrecy ───────────────────────────────────────────────────────
# DSM-5: "has lied to conceal the extent of involvement with gambling"
DECEPTION = [
    "hiding my gambling", "hiding gambling from my family",
    "lying about gambling", "lying to my partner about gambling",
    "lying to my wife about gambling", "lying to my husband about gambling",
    "secret gambling account", "gambling in secret",
    "deleted my betting history", "hiding transactions",
]

# ── Explicit tool requests ────────────────────────────────────────────────────
# Player-initiated requests for RG tools — highest intent signal
TOOL_REQUESTS = [
    "self exclude", "self-exclude", "self exclusion", "self-exclusion",
    "close my account", "block my account", "freeze my account",
    "delete my account", "deactivate my account",
    "deposit limit", "spending limit", "loss limit", "wager limit",
    "session limit", "time limit on my account",
    "cooling off", "cooling-off period", "take a break",
    "pause my account", "temporary block",
    "need help with gambling", "help me stop gambling", "help me stop",
    "gamstop", "gamban", "gambling blocker",
    "self-assessment", "gambling quiz", "am i a problem gambler",
    "responsible gaming tools", "safer gambling tools",
]

# ── Relationship & social harm ────────────────────────────────────────────────
SOCIAL_HARM = [
    "gambling affecting my family", "gambling affecting my relationship",
    "gambling affecting my marriage", "gambling affecting my work",
    "affecting my family", "affecting my relationship",
    "partner upset about my gambling", "wife upset about gambling",
    "husband upset about gambling", "argument about gambling",
    "family intervention about gambling",
    "addicted to gambling", "gambling addiction", "gambling problem",
    "problem gambler", "compulsive gambler", "compulsive gambling",
]

# ── General / catch-all ───────────────────────────────────────────────────────
GENERAL = [
    "cannot control", "can't control my gambling", "out of control",
    "losing control", "lost control of gambling",
    "spend too much", "spending too much",
    "cannot control my spending",
]

RG_KEYWORDS = (
    LOSS_OF_CONTROL
    + PREOCCUPATION
    + CHASING
    + ESCAPISM
    + FINANCIAL_HARM
    + WITHDRAWAL
    + DECEPTION
    + TOOL_REQUESTS
    + SOCIAL_HARM
    + GENERAL
)

SAFE_RESPONSE = (
    "Thank you for reaching out. Recognising when gambling may be affecting you "
    "is an important step.\n\n"
    "We offer a range of responsible gaming tools including:\n"
    "• Deposit limits (daily, weekly, monthly)\n"
    "• Session time limits\n"
    "• Cooling-off periods (24 hours to 30 days)\n"
    "• Self-exclusion (6 months to permanent)\n\n"
    "You can access these in the Responsible Gaming section of your Account Settings, "
    "or our support team can help you set them up right now via live chat.\n\n"
    "If you would like to speak with someone, free confidential support is available "
    "through gambling helplines in your country."
)


def check(message: str) -> dict:
    normalised = message.lower()
    for keyword in RG_KEYWORDS:
        if keyword in normalised:
            return {"signal": True, "response": SAFE_RESPONSE}
    return {"signal": False, "response": ""}
