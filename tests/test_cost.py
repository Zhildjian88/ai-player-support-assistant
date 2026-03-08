"""
test_cost.py
Cost recording, p95 calculation, and summary field completeness.
"""
import sys
sys.path.insert(0, '.')
import pytest
from app.cost_service import record, get_summary

REQUIRED_FIELDS = [
    "total_llm_calls","successful_calls","failed_calls",
    "total_input_tokens","total_output_tokens","total_tokens",
    "total_cost_usd","avg_cost_per_call_usd","avg_latency_ms",
    "p95_latency_ms","llm_call_rate","total_queries_routed",
    "today_llm_calls","today_cost_usd",
    "most_expensive_session","model_breakdown",
]

def test_summary_has_all_required_fields():
    summary = get_summary()
    for field in REQUIRED_FIELDS:
        assert field in summary, f"Missing field: {field}"

def test_record_and_retrieve():
    before = get_summary()["total_llm_calls"]
    record("test-cost-01","U1001","llama-3.1-8b-instant",200,100,True,500)
    after  = get_summary()["total_llm_calls"]
    assert after == before + 1

def test_failed_call_recorded():
    before = get_summary()["failed_calls"]
    record("test-cost-02","U1001","llama-3.1-8b-instant",0,0,False,30)
    after  = get_summary()["failed_calls"]
    assert after == before + 1

def test_cost_is_positive_for_successful_call():
    record("test-cost-03","U1001","llama-3.1-8b-instant",300,150,True,600)
    summary = get_summary()
    assert summary["total_cost_usd"] > 0

def test_p95_latency_is_not_none_with_data():
    # Seed varied latencies
    for lat in [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]:
        record("p95-test","U1001","llama-3.1-8b-instant",50,50,True,lat)
    summary = get_summary()
    assert summary["p95_latency_ms"] is not None
    assert summary["p95_latency_ms"] >= summary["avg_latency_ms"]

def test_llm_call_rate_is_string_percentage():
    summary = get_summary()
    rate = summary["llm_call_rate"]
    assert isinstance(rate, str)
    assert "%" in rate

def test_model_breakdown_is_list():
    summary = get_summary()
    assert isinstance(summary["model_breakdown"], list)
