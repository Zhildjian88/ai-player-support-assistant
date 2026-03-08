"""
test_similarity.py — Day 3 validation suite

Tests the similarity_service in isolation and via the router.
Covers: index build, threshold behaviour, retrieval accuracy,
multilingual response selection, audit metadata, router priority.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

# Stub LLM before importing router
import app.llm_service as llm
llm.call = lambda msg, uid=None, lang="": {"response": "LLM stub", "model": "stub"}

from app.similarity_service import search, get_index_stats
from app.router import process_message


# ── Index ────────────────────────────────────────────────────────────────────

def test_index_builds():
    stats = get_index_stats()
    assert stats["index_entries"] > 0,  "FAISS index must have entries"
    assert stats["index_dim"] > 0,      "Index dimension must be positive"
    assert stats["backend"] in ("neural", "tfidf")


def test_index_has_all_sources():
    stats = get_index_stats()
    # 15 approved + 30 FAQ + 12 game anchors = 57
    assert stats["corpus_anchors"] >= 51


# ── Threshold ────────────────────────────────────────────────────────────────

def test_nonsense_query_rejected():
    r = search("xyzzy frobble quantum banana xkcd", "en")
    assert not r["matched"], "Nonsense query should not match"
    assert r["score"] < r["threshold"]


def test_very_short_query_handled():
    r = search("hi", "en")
    # May or may not match — must not raise an exception
    assert isinstance(r["matched"], bool)
    assert "score" in r


# ── Retrieval ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("msg,expected_type", [
    ("how does blackjack work",             "game_rules"),
    ("how long does kyc verification take", "faq"),
    ("roulette how to bet on red numbers",  "game_rules"),
    ("what documents do i need for kyc",    "faq"),
])
def test_english_retrieval_source_type(msg, expected_type):
    r = search(msg, "en")
    assert r["matched"], f"Expected match for: {msg}"
    assert r["source_type"] == expected_type, \
        f"Expected {expected_type}, got {r['source_type']} (score={r['score']})"


# ── Multilingual response selection ──────────────────────────────────────────

@pytest.mark.parametrize("lang", ["en", "th", "id", "vi", "ms", "tl"])
def test_approved_answer_returns_language_variant(lang):
    r = search("withdrawal is pending", lang)
    assert r["matched"], f"Should match 'withdrawal is pending' for lang={lang}"
    assert len(r["response"]) > 10, "Response should not be empty"


# ── Audit metadata ────────────────────────────────────────────────────────────

def test_audit_metadata_completeness():
    r = search("my account has been locked", "en")
    required = ["matched", "response", "score", "source_id",
                "source_type", "backend", "threshold"]
    for field in required:
        assert field in r, f"Missing audit field: {field}"


def test_score_is_float_in_range():
    r = search("how does blackjack work", "en")
    assert isinstance(r["score"], float)
    assert 0.0 <= r["score"] <= 1.0


# ── Router priority order ────────────────────────────────────────────────────

@pytest.mark.parametrize("msg,uid,expected_route", [
    ("how do I beat the casino",                   None,    "policy_guardrail"),
    ("I lost everything and want to die",          None,    "distress_detector"),
    ("I cannot stop gambling and need help",       None,    "rg_detector"),
    ("someone logged into my account from abroad", None,    "fraud_detector"),
    ("what is my kyc status",                      "U1003", "account_service"),
    ("why is my withdrawal pending",               "U1001", "payment_service"),
    ("what promotions are available today",        "U1001", "promotions_service"),
    ("how does blackjack work",                    None,    "game_rules_service"),
    ("how long does kyc verification take",        None,    "faq_service"),
])
def test_router_priority_order(msg, uid, expected_route):
    r = process_message(msg, uid)
    assert r["route_taken"] == expected_route, \
        f"Expected {expected_route}, got {r['route_taken']}"


def test_similarity_route_carries_audit_metadata():
    """
    When similarity_service fires, the router result should include
    similarity_meta with source_id, source_type, backend, score, threshold.
    """
    # Use a query that clears deterministic routes and hits similarity
    r = process_message("my bonus expired before i could use it", None)
    if r["route_taken"] == "similarity_service":
        meta = r.get("similarity_meta", {})
        assert "source_id"   in meta
        assert "source_type" in meta
        assert "backend"     in meta
        assert "score"       in meta
        assert "threshold"   in meta


def test_decision_trace_fields_complete():
    """Every response must carry the full decision trace."""
    r = process_message("how does blackjack work", None)
    required = ["response", "language", "route_taken", "source",
                "intent", "confidence", "risk_level", "risk_flags",
                "escalated", "llm_called", "audit_id", "session_id"]
    for field in required:
        assert field in r, f"Missing decision trace field: {field}"
