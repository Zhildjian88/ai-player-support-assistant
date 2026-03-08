"""
cost_service.py
Records LLM token usage and estimated cost per call.

Vendor-neutral: works with any LLM provider (Anthropic, Groq, etc.).
The model field in each log row identifies which provider and model
was used. Cost estimates use configurable per-token rates below.

Default pricing reference (Groq llama-3.1-8b-instant, as of 2025):
    Input:  $0.80 per 1M tokens
    Output: $4.00 per 1M tokens

If using Groq (llama-3.1-8b-instant, as of 2025):
    Input:  $0.05 per 1M tokens
    Output: $0.08 per 1M tokens

Update COST_PER_INPUT_TOKEN and COST_PER_OUTPUT_TOKEN below to match
your active provider. The log still records the actual model string
returned by the API, so per-model breakdown is always accurate.

Stored in llm_cost_log table. Exposed via GET /cost/summary.

Fields recorded per call:
    session_id       — for per-session breakdown
    user_id          — for per-user analysis
    model            — exact model string returned by API
    input_tokens     — from API usage object
    output_tokens    — from API usage object
    estimated_cost_usd
    llm_success      — 0 if API call failed
    latency_ms       — wall-clock time of API call
    route            — always 'llm_fallback' for now
"""

from datetime import datetime, timezone
from app.db_init import get_connection

# Pricing per token (USD) — update to match your active LLM provider
# Anthropic Claude Haiku:  input $0.80/1M,  output $4.00/1M  (if switching back)
# Groq llama-3.1-8b:       input $0.05/1M,  output $0.08/1M
COST_PER_INPUT_TOKEN  = 0.05  / 1_000_000   # Groq llama-3.1-8b-instant
COST_PER_OUTPUT_TOKEN = 0.08  / 1_000_000   # Groq llama-3.1-8b-instant
# Anthropic Haiku rates: input $0.80/1M, output $4.00/1M — update if switching providers


def record(
    session_id:   str,
    user_id:      str | None,
    model:        str,
    input_tokens: int,
    output_tokens:int,
    llm_success:  bool,
    latency_ms:   int,
    route:        str = "llm_fallback",
):
    cost = (input_tokens * COST_PER_INPUT_TOKEN +
            output_tokens * COST_PER_OUTPUT_TOKEN)

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO llm_cost_log
               (session_id, user_id, model, input_tokens, output_tokens,
                total_tokens, estimated_cost_usd, llm_success, latency_ms,
                route, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                session_id,
                user_id or "anonymous",
                model,
                input_tokens,
                output_tokens,
                input_tokens + output_tokens,
                round(cost, 8),
                1 if llm_success else 0,
                latency_ms,
                route,
                datetime.now(timezone.utc).isoformat(),
            )
        )
        conn.commit()
    except Exception as e:
        print(f"[cost_service] Warning: {e}")
    finally:
        conn.close()


def get_summary() -> dict:
    """
    Returns aggregate cost and usage statistics.
    Exposed via GET /cost/summary.
    """
    conn = get_connection()
    try:
        # Overall LLM stats
        row = conn.execute("""
            SELECT
                COUNT(*)                        AS total_llm_calls,
                SUM(input_tokens)               AS total_input_tokens,
                SUM(output_tokens)              AS total_output_tokens,
                SUM(total_tokens)               AS total_tokens,
                SUM(estimated_cost_usd)         AS total_cost_usd,
                AVG(estimated_cost_usd)         AS avg_cost_per_call,
                AVG(latency_ms)                 AS avg_latency_ms,
                SUM(CASE WHEN llm_success=1 THEN 1 ELSE 0 END) AS successful_calls,
                SUM(CASE WHEN llm_success=0 THEN 1 ELSE 0 END) AS failed_calls
            FROM llm_cost_log
        """).fetchone()

        # p95 latency — 95th percentile of successful call latencies
        latency_rows = conn.execute(
            "SELECT latency_ms FROM llm_cost_log WHERE llm_success=1 ORDER BY latency_ms ASC"
        ).fetchall()
        p95_latency_ms = None
        if latency_rows:
            idx = max(0, int(len(latency_rows) * 0.95) - 1)
            p95_latency_ms = latency_rows[idx][0]

        # Total routed queries (for LLM call rate)
        total_queries = conn.execute(
            "SELECT COUNT(*) FROM audit_log"
        ).fetchone()[0] or 1

        # Most expensive session
        top_session = conn.execute("""
            SELECT session_id, SUM(estimated_cost_usd) AS session_cost
            FROM llm_cost_log
            GROUP BY session_id
            ORDER BY session_cost DESC
            LIMIT 1
        """).fetchone()

        # Today's costs
        today = datetime.now(timezone.utc).date().isoformat()
        today_row = conn.execute("""
            SELECT COUNT(*) AS calls, SUM(estimated_cost_usd) AS cost
            FROM llm_cost_log
            WHERE timestamp >= ?
        """, (today,)).fetchone()

        # Per-model breakdown
        models = conn.execute("""
            SELECT model, COUNT(*) AS calls, SUM(estimated_cost_usd) AS cost
            FROM llm_cost_log
            GROUP BY model
        """).fetchall()

        llm_calls    = row["total_llm_calls"] or 0
        llm_call_rate= f"{round(llm_calls / total_queries * 100, 1)}%"

        return {
            "total_llm_calls":       llm_calls,
            "successful_calls":      row["successful_calls"] or 0,
            "failed_calls":          row["failed_calls"] or 0,
            "total_input_tokens":    row["total_input_tokens"] or 0,
            "total_output_tokens":   row["total_output_tokens"] or 0,
            "total_tokens":          row["total_tokens"] or 0,
            "total_cost_usd":        round(row["total_cost_usd"] or 0, 6),
            "avg_cost_per_call_usd": round(row["avg_cost_per_call"] or 0, 6),
            "avg_latency_ms":        round(row["avg_latency_ms"] or 0, 1),
            "p95_latency_ms":        p95_latency_ms,
            "llm_call_rate":         llm_call_rate,
            "total_queries_routed":  total_queries,
            "today_llm_calls":       today_row["calls"] or 0,
            "today_cost_usd":        round(today_row["cost"] or 0, 6),
            "most_expensive_session": dict(top_session) if top_session else None,
            "model_breakdown":       [dict(m) for m in models],
        }
    finally:
        conn.close()
