"""
promotions_service.py
Returns active promotions from SQLite (seeded from promotions.json).
Filters by active status and optionally by user country/segment.
"""

import json

PROMO_TRIGGERS = [
    "promotion", "promo", "free spins", "reload bonus",
    "welcome bonus", "what promotions", "active promotions",
    "available offers", "current offers", "deals",
    "what bonus", "show me bonus", "check my bonus",
    "my cashback", "cashback offer",
]

# These indicate the player is asking a question ABOUT a bonus, not requesting the list
PROMO_EXCLUSIONS = [
    "what happens to my bonus",
    "if i change", "if i cancel", "if i withdraw",
    "bonus expire", "bonus lost", "lose my bonus",
    "bonus terms", "bonus conditions", "wagering requirement",
    "how does the bonus work", "how do bonuses work",
]


def lookup(message: str, user_id: str | None = None) -> dict:
    from app.db_init import get_connection
    normalised = message.lower()

    if any(e in normalised for e in PROMO_EXCLUSIONS):
        return {"matched": False, "response": ""}
    if not any(t in normalised for t in PROMO_TRIGGERS):
        return {"matched": False, "response": ""}

    conn  = get_connection()
    rows  = conn.execute(
        "SELECT * FROM promotions WHERE active = 1 ORDER BY promotion_id"
    ).fetchall()

    user_country = None
    if user_id:
        u = conn.execute(
            "SELECT country FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if u:
            user_country = u["country"]

    conn.close()

    if not rows:
        return {"matched": True, "response": "There are no active promotions at this time. Please check back soon."}

    promos = []
    for r in rows:
        p = dict(r)
        eligibility = json.loads(p["country_eligibility"]) if p["country_eligibility"] else []
        if user_country and eligibility and user_country not in eligibility:
            continue
        promos.append(p)

    if not promos:
        return {"matched": True, "response": "There are no promotions currently available in your region."}

    lines = ["Here are the currently active promotions:\n"]
    for p in promos[:5]:  # Cap at 5 for readability
        lines.append(f"**{p['title']}**")
        lines.append(f"{p['description']}")
        if p["wagering_requirement"]:
            lines.append(f"Wagering requirement: {p['wagering_requirement']}x")
        lines.append("")

    lines.append("Full terms and conditions apply. Visit our Promotions page for details.")
    return {"matched": True, "response": "\n".join(lines)}
