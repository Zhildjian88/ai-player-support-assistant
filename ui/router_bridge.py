"""
router_bridge.py
Thin adapter used by both Streamlit UIs.

Mode detection (automatic):
    STREAMLIT_CLOUD=true  → in-process mode (router called directly, no FastAPI)
    USE_INPROCESS=true    → force in-process mode locally
    otherwise             → HTTP mode (calls FastAPI at API_URL)

Local dev: if FastAPI is not running, falls back to in-process automatically.
"""

import os
import sys
import uuid

# Ensure project root is on path so app.* imports work
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Mode detection ────────────────────────────────────────────
_API_URL      = os.getenv("API_URL", "http://localhost:8000")
_IS_CLOUD     = os.getenv("STREAMLIT_CLOUD", "").lower() in ("1", "true", "yes")
_FORCE_LOCAL  = os.getenv("USE_INPROCESS", "").lower() in ("1", "true", "yes")
_IS_LOCALHOST = "localhost" in _API_URL or "127.0.0.1" in _API_URL
USE_INPROCESS = _IS_CLOUD or _FORCE_LOCAL

_db_ready = False


# ── Public API ────────────────────────────────────────────────

def chat(message: str, user_id: str, session_id: str, lang: str = "en") -> dict:
    """
    Send a chat message. Returns same dict shape as FastAPI /chat:
        response, route_taken, risk_level, risk_flags, language,
        escalated, llm_called, confidence, intent, session_id, audit_id
    """
    if USE_INPROCESS:
        return _inprocess_chat(message, user_id, session_id)
    try:
        return _api_chat(message, user_id, session_id, lang)
    except Exception:
        if _IS_LOCALHOST:
            # FastAPI not running locally — fall back silently
            return _inprocess_chat(message, user_id, session_id)
        raise


def get(endpoint: str, timeout: int = 5):
    """
    GET wrapper for ops console tabs (audit, escalations, cost, metrics).
    Returns parsed JSON dict/list, or None if unreachable.
    """
    if USE_INPROCESS:
        return _inprocess_get(endpoint)
    try:
        import requests
        resp = requests.get(f"{_API_URL}{endpoint}", timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        if _IS_LOCALHOST:
            return _inprocess_get(endpoint)
        return None


# ── HTTP mode ─────────────────────────────────────────────────

def _api_chat(message, user_id, session_id, lang):
    import requests
    payload = {
        "message":    message,
        "user_id":    user_id,
        "session_id": session_id,
    }
    resp = requests.post(f"{_API_URL}/chat", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── In-process mode ───────────────────────────────────────────

def _ensure_db():
    """Initialise SQLite on first run (Streamlit Cloud has no db_init step)."""
    try:
        from app.db_init import get_connection, init
        conn = get_connection()
        conn.execute("SELECT 1 FROM users LIMIT 1")
        conn.close()
    except Exception:
        try:
            from app import db_init
            db_init.init()
        except Exception as e:
            print(f"[router_bridge] db init warning: {e}")


def _inprocess_chat(message: str, user_id: str, session_id: str) -> dict:
    global _db_ready
    if not _db_ready:
        _ensure_db()
        _db_ready = True

    # Bug fix: correct function name is process_message, not route
    # Bug fix: process_message does not accept lang parameter
    from app.router import process_message
    result = process_message(
        message    = message,
        user_id    = user_id,
        session_id = session_id or str(uuid.uuid4()),
    )
    return result


def _inprocess_get(endpoint: str):
    """
    Serve ops console data directly from DB for in-process mode.
    Mirrors exactly what main.py does in each endpoint.
    """
    global _db_ready
    if not _db_ready:
        _ensure_db()
        _db_ready = True

    try:
        from app.db_init import get_connection

        # /audit/recent
        if endpoint.startswith("/audit/recent"):
            limit = 20
            if "limit=" in endpoint:
                try:
                    limit = int(endpoint.split("limit=")[-1].split("&")[0])
                except ValueError:
                    pass
            conn = get_connection()
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]

        # /escalations/open
        elif endpoint.startswith("/escalations/open"):
            conn = get_connection()
            rows = conn.execute(
                "SELECT * FROM escalation_queue WHERE status='open' ORDER BY created_at DESC"
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]

        # /cost/summary — Bug fix: function is get_summary, not get_metrics
        elif endpoint.startswith("/cost"):
            from app.cost_service import get_summary
            return get_summary()

        # /metrics — Bug fix: function is get_metrics, not get_summary
        elif endpoint.startswith("/metrics"):
            from app.metrics_service import get_metrics
            return get_metrics()

        elif endpoint.startswith("/health"):
            return {"status": "ok", "mode": "in-process"}

    except Exception as e:
        print(f"[router_bridge] in-process GET {endpoint} error: {e}")

    return None
