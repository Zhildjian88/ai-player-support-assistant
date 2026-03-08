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


# Stop words that don't count as content matches
STOP_WORDS = {
    "how", "do", "i", "my", "a", "an", "the", "is", "are", "was",
    "can", "what", "why", "when", "where", "who", "will", "to",
    "in", "on", "at", "for", "of", "and", "or", "it", "be", "does",
    "did", "has", "have", "get", "set", "this", "that", "with", "me",
    "you", "we", "they", "not", "if", "so", "up", "out", "about",
}

def lookup(message: str) -> dict:
    _load()
    normalised = message.lower()
    m_words = set(normalised.split())
    m_content = m_words - STOP_WORDS  # meaningful words only

    best_score = 0
    best_answer = ""

    for entry in _faq_data:
        q_words = set(entry["question"].lower().split())
        q_content = q_words - STOP_WORDS

        # Must share at least one content word — prevents "how do I X" matching "how do I Y"
        content_overlap = len(q_content & m_content)
        if content_overlap == 0:
            continue

        overlap = len(q_words & m_words)
        score   = overlap / max(len(q_words), 1)
        if score > best_score:
            best_score  = score
            best_answer = entry["answer"]

    if best_score >= 0.50:
        return {"matched": True, "response": best_answer}
    return {"matched": False, "response": ""}
