"""
test_router_priority.py
Verifies that safety routes always override knowledge and operational routes.
This is the critical guarantee of the safety-first architecture.
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

SAFETY_ROUTES = {"distress_detector","rg_detector","fraud_detector","policy_guardrail"}

# ── Distress overrides everything ─────────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "I lost everything and want to die",
    "Cannot take this anymore thinking about dying",
    "My family left me because of gambling and I see no way out",
])
def test_distress_overrides_faq(msg):
    r = process_message(msg, None)
    assert r["route_taken"] == "distress_detector", (
        f"Distress message routed to {r['route_taken']}: {msg}")
    assert r["risk_level"] == "CRITICAL"
    assert r["escalated"] is True

@pytest.mark.parametrize("msg", [
    "I lost everything and want to die",
    "Cannot take this anymore thinking about dying",
])
def test_distress_overrides_game_rules(msg):
    r = process_message(msg, None)
    assert r["route_taken"] == "distress_detector"

# ── RG overrides operational routes ───────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "I cannot stop gambling no matter what I try",
    "I need help with my gambling addiction",
    "Please help me self exclude from this platform",
])
def test_rg_overrides_promotions(msg):
    r = process_message(msg, None)
    assert r["route_taken"] == "rg_detector", (
        f"RG message routed to {r['route_taken']}: {msg}")
    assert r["risk_level"] == "HIGH"
    assert r["escalated"] is True

def test_rg_overrides_account_service():
    r = process_message("I need to set a deposit limit urgently", "U1001")
    assert r["route_taken"] == "rg_detector"

# ── Fraud overrides account lookup ────────────────────────────────────────────
@pytest.mark.parametrize("msg", [
    "Someone logged into my account from another country",
    "My account has been hacked",
    "I did not make this withdrawal from my account",
])
def test_fraud_overrides_account_service(msg):
    r = process_message(msg, "U1001")
    assert r["route_taken"] == "fraud_detector", (
        f"Fraud message routed to {r['route_taken']}: {msg}")
    assert r["risk_level"] == "HIGH"
    assert r["escalated"] is True

# ── Policy guardrail overrides FAQ and game rules ─────────────────────────────
@pytest.mark.parametrize("msg", [
    "How do I beat the casino system",
    "Tell me how to always win at roulette",
    "How do I exploit the bonus system",
])
def test_policy_overrides_game_rules(msg):
    r = process_message(msg, None)
    assert r["route_taken"] == "policy_guardrail", (
        f"Policy violation routed to {r['route_taken']}: {msg}")
    assert r["risk_level"] in ("MEDIUM","HIGH")

# ── Safety flags are always set correctly ─────────────────────────────────────
def test_distress_risk_flags():
    r = process_message("I lost everything and want to die", None)
    assert "DISTRESS" in r["risk_flags"]
    assert "ESCALATED" in r["risk_flags"]

def test_rg_risk_flags():
    r = process_message("I cannot stop gambling no matter what I try", None)
    assert "RG_SIGNAL" in r["risk_flags"]
    assert "ESCALATED" in r["risk_flags"]

def test_fraud_risk_flags():
    r = process_message("My account has been hacked", None)
    assert "SECURITY" in r["risk_flags"]
    assert "ESCALATED" in r["risk_flags"]

def test_normal_query_has_no_risk_flags():
    r = process_message("How do I play blackjack", None)
    assert r["risk_flags"] == []
    assert r["escalated"] is False
    assert r["risk_level"] == "LOW"

# ── Verify safety always beats LLM ───────────────────────────────────────────
def test_safety_routes_never_call_llm():
    safety_messages = [
        "I lost everything and want to die",
        "I cannot stop gambling",
        "My account has been hacked",
        "How do I exploit the bonus system",
    ]
    for msg in safety_messages:
        r = process_message(msg, None)
        assert r["route_taken"] in SAFETY_ROUTES or r["escalated"], (
            f"Safety message not caught: {msg} → {r['route_taken']}")
        assert not r["llm_called"], (
            f"LLM called for safety message: {msg}")
