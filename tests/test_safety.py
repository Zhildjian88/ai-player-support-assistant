"""
test_safety.py
Edge case tests for all four safety detectors.
"""
import sys
sys.path.insert(0, '.')
import pytest
import app.llm_service as llm_mod

def _stub(message=None, user_id=None, lang_instruction="", session_context=None):
    return {"response":"stub","model":"stub","input_tokens":0,
            "output_tokens":0,"llm_success":True,"latency_ms":0}
llm_mod.call = _stub

from app.router import process_message

# ── Distress detector ─────────────────────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "I want to end it all",
    "I have nothing left to live for",
    "I destroyed my life with gambling",
    "I borrowed from loan sharks and cannot pay back",
])
def test_distress_detected(msg):
    r = process_message(msg, None)
    assert r["route_taken"] == "distress_detector"
    assert r["risk_level"] == "CRITICAL"
    assert r["escalated"] is True

# ── RG detector ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "I want to self exclude",
    "I need a cooling off period",
    "I think I have a gambling problem",
    "Please freeze my account I am out of control",
])
def test_rg_detected(msg):
    r = process_message(msg, None)
    assert r["route_taken"] == "rg_detector"
    assert r["risk_level"] == "HIGH"

# ── Fraud detector ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "Someone logged into my account",
    "I was phished and someone accessed my account",
    "Unauthorised access to my account",
    "I did not authorise this deposit",
])
def test_fraud_detected(msg):
    r = process_message(msg, None)
    assert r["route_taken"] == "fraud_detector"
    assert r["risk_level"] == "HIGH"
    assert r["escalated"] is True

# ── Policy guardrail ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "How do I beat the casino",
    "guaranteed strategy to win",
    "how to cheat at blackjack",
    "exploit the bonus system",
])
def test_policy_blocked(msg):
    r = process_message(msg, None)
    assert r["route_taken"] == "policy_guardrail"

# ── Normal queries are not caught by safety ───────────────────────────────────
@pytest.mark.parametrize("msg", [
    "How do I play roulette",
    "What is the minimum deposit",
    "When will my withdrawal arrive",
])
def test_normal_not_caught_by_safety(msg):
    r = process_message(msg, None)
    assert r["route_taken"] not in (
        "distress_detector","rg_detector","fraud_detector")
    assert r["risk_level"] == "LOW"
