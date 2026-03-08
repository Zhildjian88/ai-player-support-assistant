"""
context_service.py
Bounded session context window for LLM-handled conversations.

Stores up to MAX_TURNS prior turns per session_id in SQLite.
Passed as conversation history to the Claude API to support
follow-up questions within the same session.

Design constraints:
    - Max 5 turns (10 messages: 5 user + 5 assistant)
    - Only used by the LLM fallback — deterministic routes ignore context
    - Oldest turns pruned automatically when limit is exceeded
    - Context is session-scoped, not user-scoped
"""

from datetime import datetime, timezone
from app.db_init import get_connection

MAX_TURNS = 5   # Max prior turn pairs to include in LLM context


def get_context(session_id: str) -> list[dict]:
    """
    Returns up to MAX_TURNS prior turns as a list of
    {"role": "user"|"assistant", "content": str} dicts.
    Ordered oldest-first as required by standard LLM chat APIs (Anthropic, Groq, OpenAI).
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT role, content FROM conversation_context
           WHERE session_id = ?
           ORDER BY turn_index ASC
           LIMIT ?""",
        (session_id, MAX_TURNS * 2)   # pairs = 2 messages per turn
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def store_turn(session_id: str, user_message: str, assistant_response: str):
    """
    Stores a user+assistant turn pair and prunes oldest turns
    if the session exceeds MAX_TURNS.
    """
    conn = get_connection()
    try:
        # Get current max turn_index for this session
        row = conn.execute(
            "SELECT MAX(turn_index) FROM conversation_context WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        next_index = (row[0] or 0) + 1
        ts = datetime.now(timezone.utc).isoformat()

        conn.execute(
            "INSERT INTO conversation_context (session_id, role, content, turn_index, timestamp) VALUES (?,?,?,?,?)",
            (session_id, "user", user_message[:1000], next_index, ts)
        )
        conn.execute(
            "INSERT INTO conversation_context (session_id, role, content, turn_index, timestamp) VALUES (?,?,?,?,?)",
            (session_id, "assistant", assistant_response[:1000], next_index, ts)
        )

        # Prune oldest turns beyond MAX_TURNS
        conn.execute(
            """DELETE FROM conversation_context
               WHERE session_id = ? AND turn_index <= (
                   SELECT MAX(turn_index) - ? FROM conversation_context
                   WHERE session_id = ?
               )""",
            (session_id, MAX_TURNS, session_id)
        )
        conn.commit()
    except Exception as e:
        print(f"[context_service] Warning: {e}")
    finally:
        conn.close()


def clear_context(session_id: str):
    """Clears all context for a session (e.g. on explicit reset)."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM conversation_context WHERE session_id = ?", (session_id,)
    )
    conn.commit()
    conn.close()
