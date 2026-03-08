"""
policy_guardrail.py
Blocks queries seeking guaranteed winning strategies, system exploitation,
casino cheating advice, RNG manipulation, weapons/harmful content,
or any topic entirely outside the scope of player support.

Sources:
  - Common operator policy violation categories
  - UKGC / MGA terms of service violation typologies
  - Standard content moderation best practices

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

# ── Weapons / harmful content ─────────────────────────────────────────────────
# Requests for information that could cause real-world harm.
# Blocked regardless of framing (research, prevention, curiosity, professional).
HARMFUL_PATTERNS = [
    # Explosives / bombs
    "build a bomb", "make a bomb", "how to make a bomb", "how to build a bomb",
    "construct a bomb", "assemble a bomb", "detonate a bomb",
    "make an explosive", "build an explosive", "create explosive",
    "how to make explosives", "improvised explosive", "ied",
    "pipe bomb", "fertilizer bomb", "nail bomb",
    # Weapons
    "make a weapon", "build a weapon", "make a gun", "build a gun",
    "make a knife to kill", "how to poison someone",
    "how to make poison", "make poison",
    # Drugs
    "how to make meth", "how to make drugs", "synthesize drugs",
    "cook meth", "make cocaine",
    # Hacking / cybercrime (distinct from casino hacking above)
    "how to hack a bank", "hack someone's account", "steal credit card",
    "how to steal money from", "commit fraud",
]

HARMFUL_RESPONSE = (
    "I'm sorry, but I'm unable to help with that request. "
    "This assistant is here to support you with your SiDOBet account, "
    "payments, game rules, promotions, and responsible gaming.\n\n"
    "If you have a support question, please feel free to ask and I'll be happy to help."
)

# ── Out-of-scope topics ───────────────────────────────────────────────────────
# Completely unrelated topics that the LLM should not attempt to answer,
# preventing hallucination of irrelevant or incorrect information.
OUT_OF_SCOPE_PATTERNS = [
    "capital of ", "who is the president", "who is the prime minister",
    "what is the population", "what is the weather", "weather today",
    "stock price", "stock market", "cryptocurrency price", "bitcoin price",
    "sports score", "football score", "match score",
    "recipe for ", "how to cook", "how to bake",
    "medical advice", "symptoms of ", "diagnose me",
    "legal advice", "should i sue", "is it legal to",
    "tell me a joke", "write me a poem", "write a story",
    "translate this", "what language is",
    "who invented ", "when was ", "history of ",
]

OUT_OF_SCOPE_RESPONSE = (
    "I'm your SiDOBet support assistant, so I'm only able to help with "
    "account queries, payments, game rules, promotions, and responsible gaming.\n\n"
    "Is there anything related to your SiDOBet account I can help you with?"
)

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
    Checks in order: harmful content → prohibited gambling patterns → out of scope
    """
    normalised = message.lower()

    # 1. Harmful / dangerous content — hard block
    for pattern in HARMFUL_PATTERNS:
        if pattern in normalised:
            return {"blocked": True, "response": HARMFUL_RESPONSE}

    # 2. Prohibited gambling patterns
    for pattern in PROHIBITED_PATTERNS:
        if pattern in normalised:
            return {"blocked": True, "response": SAFE_RESPONSE}

    # 3. Out of scope — redirect cleanly rather than letting LLM hallucinate
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if pattern in normalised:
            return {"blocked": True, "response": OUT_OF_SCOPE_RESPONSE}

    return {"blocked": False, "response": ""}
