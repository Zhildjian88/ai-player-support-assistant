"""
faq_service.py
Simple keyword-based FAQ lookup against faq.json.
Used after semantic search as a lightweight fallback.
"""

import json
from pathlib import Path

_faq_data = None

def _load():
    global _faq_data
    if _faq_data is None:
        path = Path(__file__).parent.parent / "data" / "faq.json"
        with open(path) as f:
            _faq_data = json.load(f)


def lookup(message: str) -> dict:
    _load()
    normalised = message.lower()
    best_score = 0
    best_answer = ""

    for entry in _faq_data:
        q_words = set(entry["question"].lower().split())
        m_words = set(normalised.split())
        overlap = len(q_words & m_words)
        score   = overlap / max(len(q_words), 1)
        if score > best_score:
            best_score  = score
            best_answer = entry["answer"]

    if best_score >= 0.35:
        return {"matched": True, "response": best_answer}
    return {"matched": False, "response": ""}
