"""
game_rules_service.py
Returns game rules from game_rules.json based on keyword detection.
"""

import json
from pathlib import Path

_rules_data = None

GAME_KEYWORDS = {
    "blackjack": ["blackjack", "black jack", "21"],
    "roulette":  ["roulette"],
    "baccarat":  ["baccarat"],
    "slots":     ["slot", "slots", "rtp", "payline", "scatter", "wild symbol", "volatility"],
    "poker":     ["poker", "three card", "three-card"],
    "sports_betting": ["sports bet", "parlay", "over under", "moneyline", "asian handicap",
                       "point spread", "odds", "accumulator"],
}


def _load():
    global _rules_data
    if _rules_data is None:
        path = Path(__file__).parent.parent / "data" / "game_rules.json"
        with open(path) as f:
            _rules_data = json.load(f)


def lookup(message: str) -> dict:
    _load()
    normalised = message.lower()

    # Reject if this looks like a strategy/winning request
    strategy_words = ["win", "beat", "trick", "strategy", "cheat", "hack", "exploit"]
    if any(w in normalised for w in strategy_words):
        return {"matched": False, "response": ""}

    for game_key, keywords in GAME_KEYWORDS.items():
        if any(k in normalised for k in keywords):
            rule = _rules_data.get(game_key)
            if not rule:
                continue
            name    = rule["name"]
            summary = rule["summary"]
            basics  = rule.get("basic_rules", [])
            rtp     = rule.get("rtp", "")
            lines   = [f"**{name}**", "", summary, ""]
            if basics:
                lines.append("Basic rules:")
                for b in basics[:4]:
                    lines.append(f"• {b}")
            if rtp:
                lines.append(f"\nReturn to Player (RTP): {rtp}")
            return {"matched": True, "response": "\n".join(lines)}

    return {"matched": False, "response": ""}
