"""
test_services.py
Correctness tests for payment, account, and promotions services
against the seeded SQLite data. Tests call through the router to
reflect actual usage — services are invoked via router.process_message.
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

# ── Payment service ───────────────────────────────────────────────────────────
def test_payment_status_query_with_user():
    r = process_message("Why is my withdrawal pending", "U1001")
    assert r["route_taken"] == "payment_service"
    assert len(r["response"]) > 0

def test_payment_route_requires_user_id():
    # Without user_id, payment queries fall through to knowledge routes
    r = process_message("Why is my withdrawal pending", None)
    assert r["route_taken"] != "payment_service"

def test_payment_response_not_empty_for_known_user():
    r = process_message("When will my withdrawal arrive", "U1001")
    if r["route_taken"] == "payment_service":
        assert len(r["response"]) > 10

# ── Account service ───────────────────────────────────────────────────────────
def test_account_status_query_with_user():
    r = process_message("What is my account status", "U1001")
    assert r["route_taken"] == "account_service"
    assert len(r["response"]) > 0

def test_account_route_requires_user_id():
    r = process_message("What is my account status", None)
    assert r["route_taken"] != "account_service"

def test_kyc_query_routed_to_account():
    r = process_message("What is my KYC status", "U1003")
    assert r["route_taken"] == "account_service"

def test_restricted_account_handled():
    # U1004 has restricted status in seed data
    r = process_message("What is my account status", "U1004")
    assert r["route_taken"] == "account_service"
    assert len(r["response"]) > 0

# ── Promotions service ────────────────────────────────────────────────────────
def test_promotions_query_routed_correctly():
    r = process_message("What bonuses are available today", "U1001")
    assert r["route_taken"] == "promotions_service"

def test_promotions_response_not_empty():
    r = process_message("Show me all current promotions", "U1001")
    assert r["route_taken"] == "promotions_service"
    assert len(r["response"]) > 10

def test_free_spins_query_routed_to_promotions():
    r = process_message("How do I claim free spins", "U1001")
    assert r["route_taken"] == "promotions_service"
