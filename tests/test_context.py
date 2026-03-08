"""
test_context.py
Session context window storage, retrieval, and pruning boundary conditions.
"""
import sys
sys.path.insert(0, '.')
import pytest
from app.context_service import store_turn, get_context, clear_context, MAX_TURNS

SESSION = "ctx-unit-test"

def setup_function():
    clear_context(SESSION)

def test_empty_context_returns_empty_list():
    clear_context("empty-session")
    assert get_context("empty-session") == []

def test_single_turn_stored_and_retrieved():
    store_turn(SESSION, "hello", "hi there")
    ctx = get_context(SESSION)
    assert len(ctx) == 2
    assert ctx[0]["role"] == "user"
    assert ctx[0]["content"] == "hello"
    assert ctx[1]["role"] == "assistant"
    assert ctx[1]["content"] == "hi there"

def test_context_order_is_oldest_first():
    for i in range(3):
        store_turn(SESSION, f"user {i}", f"assistant {i}")
    ctx = get_context(SESSION)
    assert ctx[0]["content"] == "user 0"
    assert ctx[-1]["content"] == "assistant 2"

def test_context_pruned_at_max_turns():
    # Store MAX_TURNS + 2 turns — oldest should be pruned
    for i in range(MAX_TURNS + 2):
        store_turn(SESSION, f"u{i}", f"a{i}")
    ctx = get_context(SESSION)
    assert len(ctx) <= MAX_TURNS * 2, (
        f"Context should be bounded at {MAX_TURNS*2} messages, got {len(ctx)}")

def test_oldest_pair_removed_after_overflow():
    for i in range(MAX_TURNS + 1):
        store_turn(SESSION, f"msg{i}", f"reply{i}")
    ctx = get_context(SESSION)
    # msg0 should have been pruned
    contents = [m["content"] for m in ctx]
    assert "msg0" not in contents, "Oldest turn should have been pruned"

def test_clear_context_removes_all_turns():
    store_turn(SESSION, "test", "test")
    clear_context(SESSION)
    assert get_context(SESSION) == []

def test_context_is_session_scoped():
    other = "other-session"
    clear_context(other)
    store_turn(SESSION, "session A message", "session A reply")
    store_turn(other, "session B message", "session B reply")
    ctx_a = get_context(SESSION)
    ctx_b = get_context(other)
    assert any("session A" in m["content"] for m in ctx_a)
    assert not any("session A" in m["content"] for m in ctx_b)

def test_context_returns_dicts_with_role_and_content():
    store_turn(SESSION, "what is blackjack", "blackjack is a card game")
    ctx = get_context(SESSION)
    for msg in ctx:
        assert "role" in msg
        assert "content" in msg
        assert msg["role"] in ("user", "assistant")
