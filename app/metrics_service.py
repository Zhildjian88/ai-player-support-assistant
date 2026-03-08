"""
metrics_service.py
Exposes operational telemetry for the routing system.

Covers:
    - Total queries routed
    - Route distribution (safety, operational, knowledge, LLM)
    - Safety event count and rate
    - LLM usage rate and cost
    - Latency statistics (avg, p95)
    - Escalation queue depth
    - System health indicators

Exposed via GET /metrics on the FastAPI gateway.
"""

from app.db_init import get_connection


def get_metrics() -> dict:
    conn = get_connection()
    try:
        # ── Query volume ──────────────────────────────────────────────────────
        total_queries = conn.execute(
            "SELECT COUNT(*) FROM audit_log"
        ).fetchone()[0] or 0

        # ── Route distribution ────────────────────────────────────────────────
        route_rows = conn.execute(
            "SELECT route_taken, COUNT(*) FROM audit_log GROUP BY route_taken ORDER BY COUNT(*) DESC"
        ).fetchall()
        route_distribution = {r["route_taken"]: r[1] for r in route_rows}

        # ── Safety events ─────────────────────────────────────────────────────
        safety_routes = ("distress_detector", "rg_detector",
                         "fraud_detector", "policy_guardrail")
        safety_events = sum(
            route_distribution.get(r, 0) for r in safety_routes
        )
        safety_rate = (
            f"{round(safety_events / total_queries * 100, 1)}%"
            if total_queries else "0%"
        )

        # ── Escalations ───────────────────────────────────────────────────────
        open_escalations = conn.execute(
            "SELECT COUNT(*) FROM escalation_queue WHERE status = 'open'"
        ).fetchone()[0] or 0

        total_escalations = conn.execute(
            "SELECT COUNT(*) FROM escalation_queue"
        ).fetchone()[0] or 0

        # ── LLM usage ─────────────────────────────────────────────────────────
        llm_rows = conn.execute(
            """SELECT COUNT(*) AS calls,
                      SUM(estimated_cost_usd) AS cost,
                      AVG(latency_ms) AS avg_lat,
                      SUM(CASE WHEN llm_success=0 THEN 1 ELSE 0 END) AS failures
               FROM llm_cost_log"""
        ).fetchone()

        llm_calls   = llm_rows["calls"] or 0
        llm_cost    = round(llm_rows["cost"] or 0, 6)
        llm_avg_lat = round(llm_rows["avg_lat"] or 0, 1)
        llm_failures = llm_rows["failures"] or 0

        llm_call_rate = (
            f"{round(llm_calls / total_queries * 100, 1)}%"
            if total_queries else "0%"
        )

        # p95 latency (successful LLM calls only)
        lat_rows = conn.execute(
            "SELECT latency_ms FROM llm_cost_log WHERE llm_success=1 ORDER BY latency_ms ASC"
        ).fetchall()
        p95_latency_ms = None
        if lat_rows:
            idx = max(0, int(len(lat_rows) * 0.95) - 1)
            p95_latency_ms = lat_rows[idx][0]

        # ── Cache efficiency ──────────────────────────────────────────────────
        cache_entries = conn.execute(
            "SELECT COUNT(*) FROM cache"
        ).fetchone()[0] or 0

        cache_hits = conn.execute(
            "SELECT SUM(hit_count - 1) FROM cache"
        ).fetchone()[0] or 0

        # ── System health ─────────────────────────────────────────────────────
        # Flag if LLM failure rate exceeds 20%
        llm_health = "ok"
        if llm_calls > 0 and llm_failures / llm_calls > 0.2:
            llm_health = "degraded"

        return {
            "total_queries":        total_queries,
            "route_distribution":   route_distribution,
            "safety_events":        safety_events,
            "safety_event_rate":    safety_rate,
            "open_escalations":     open_escalations,
            "total_escalations":    total_escalations,
            "llm_calls":            llm_calls,
            "llm_call_rate":        llm_call_rate,
            "llm_failures":         llm_failures,
            "llm_total_cost_usd":   llm_cost,
            "llm_avg_latency_ms":   llm_avg_lat,
            "llm_p95_latency_ms":   p95_latency_ms,
            "llm_health":           llm_health,
            "cache_entries":        cache_entries,
            "cache_hits":           cache_hits,
        }
    finally:
        conn.close()
