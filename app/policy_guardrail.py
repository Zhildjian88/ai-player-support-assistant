"""
policy_guardrail.py
Blocks queries seeking guaranteed winning strategies, system exploitation,
casino cheating advice, or RNG manipulation.

Sources:
  - Common operator policy violation categories
  - UKGC / MGA terms of service violation typologies

When triggered: risk_level = MEDIUM, return advisory — no escalation.
NOTE: Account circumvention attempts are handled by circumvention_detector.py.
"""

PROHIBITED_PATTERNS = [
    # Beating / defeating the house
    "beat the casino", "beat the system", "beat the house",
    "outsmart the casino", "outsmart the house",

    # Guaranteed wins
    "guaranteed win", "guaranteed profit", "guaranteed strategy",
    "always win", "never lose", "cannot lose", "cant lose", "can't lose",
    "100% win", "sure win", "sure bet",
    "foolproof strategy", "foolproof system",

    # Cheating
    "cheat roulette", "cheat slots", "cheat casino",
    "cheat at blackjack", "cheat at baccarat", "cheat at poker",
    "cheat at roulette", "cheat the game",

    # Hacking / rigging
    "hack casino", "hack the game", "hack the algorithm",
    "hack the rng", "hack the slot",
    "rig the game", "rig the outcome", "rig the roulette", "rig the slots",

    # Exploiting / abusing
    "exploit the bonus", "abuse the bonus", "exploit the system",
    "exploit the rng", "exploit a glitch", "exploit a bug",
    "abuse the system", "loophole in the casino",

    # Secret tricks
    "trick to win", "secret to win", "how to win every time",
    "secret method", "secret strategy", "secret trick",
    "glitch to win",

    # False winnings
    "free money from casino", "get free money from casino",
    "get free chips", "infinite money glitch",

    # Card counting framed as a system
    "card counting system", "counting cards system",
]

SAFE_RESPONSE = (
    "I'm sorry, but I'm unable to provide advice on beating or exploiting the system. "
    "All games are independently audited and use certified random number generators "
    "to ensure fair outcomes for every player.\n\n"
    "If you'd like, I can explain how a specific game works, "
    "or share information about our responsible gaming tools "
    "such as deposit limits and session timers."
)


def check(message: str) -> dict:
    """
    Returns {"blocked": bool, "response": str}
    """
    normalised = message.lower()
    for pattern in PROHIBITED_PATTERNS:
        if pattern in normalised:
            return {"blocked": True, "response": SAFE_RESPONSE}
    return {"blocked": False, "response": ""}
