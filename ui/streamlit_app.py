"""
streamlit_app.py
Chat interface for the AI Player Support Assistant.

Features:
- Player chat interface with message history
- Mock user selector for demo purposes
- Live routing metadata display (source, risk level, language, escalation)
- Audit log viewer
- Escalation queue viewer
"""

import streamlit as st
import requests
import json
import sys
import os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from ui.router_bridge import chat as bridge_chat, get as bridge_get
from datetime import datetime

import os
API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SiDOBet Support Assistant",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.risk-LOW      { color: #28a745; font-weight: bold; }
.risk-MEDIUM   { color: #ffc107; font-weight: bold; }
.risk-HIGH     { color: #fd7e14; font-weight: bold; }
.risk-CRITICAL { color: #dc3545; font-weight: bold; }
.route-badge {
    background: #1e1e2e;
    color: #cdd6f4;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-family: monospace;
}
.escalated-badge {
    background: #dc3545;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.8em;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"   not in st.session_state: st.session_state.messages   = []
if "session_id" not in st.session_state: st.session_state.session_id = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎰 SiDOBet Support")
    st.markdown("---")

    st.subheader("Demo User")
    user_options = {
        "Anonymous (no user_id)":         None,
        "U1001 — Budi (ID, Active)":      "U1001",
        "U1002 — Somchai (TH, Gold VIP)": "U1002",
        "U1003 — James (AU, KYC Pending)":"U1003",
        "U1004 — Maria (PH, Suspended)":  "U1004",
        "U1005 — Nguyen (VN, Platinum)":  "U1005",
        "U1006 — Siriporn (TH, RG Flag)": "U1006",
        "U1007 — Ahmed (GB, Self-Excl)":  "U1007",
        "U1008 — Rizky (ID, KYC Reject)": "U1008",
        "U1009 — Tran (VN, Diamond VIP)": "U1009",
        "U1010 — Juan (PH, Gold VIP)":    "U1010",
    }
    selected_label = st.selectbox("Select demo user", list(user_options.keys()))
    user_id        = user_options[selected_label]

    st.markdown("---")
    st.subheader("Quick Test Scenarios")
    scenarios = {
        "💸 Withdrawal pending":     "Why is my withdrawal still pending?",
        "🎲 How does blackjack work": "How does blackjack work?",
        "🎁 Active promotions":       "What promotions are available today?",
        "🔐 KYC status":              "What is my KYC verification status?",
        "🚨 Suspicious login":        "Someone logged into my account from another country.",
        "🛑 Beat the casino":         "How do I beat the casino system?",
        "💔 Distress signal":         "I lost everything and I cannot take this anymore.",
        "🤝 RG signal":               "I cannot stop gambling and I need help.",
        "🇹🇭 Thai message":           "ทำไมการถอนเงินของฉันยังค้างอยู่?",
        "🇮🇩 Indonesian message":     "Kenapa penarikan saya masih pending?",
    }
    for label, msg in scenarios.items():
        if st.button(label, use_container_width=True):
            st.session_state["prefill"] = msg

    st.markdown("---")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages   = []
        st.session_state.session_id = None
        st.rerun()

    st.markdown("---")
    st.caption("AI Player Support Assistant v1.0")
    st.caption("Day 2 — Backend + UI")

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("Player Support Chat")

tab_chat, tab_audit, tab_escalations, tab_cost, tab_metrics = st.tabs([
    "💬 Chat", "📋 Audit Log", "🚨 Escalation Queue", "💰 Cost Dashboard", "📊 System Metrics"
])

# ── Chat tab ──────────────────────────────────────────────────────────────────
with tab_chat:
    # Render message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "meta" in msg:
                meta = msg["meta"]
                col1, col2, col3, col4 = st.columns(4)
                col1.markdown(
                    f'<span class="route-badge">🔀 {meta["route_taken"]}</span>',
                    unsafe_allow_html=True
                )
                risk = meta["risk_level"]
                col2.markdown(
                    f'<span class="risk-{risk}">⚠️ {risk}</span>',
                    unsafe_allow_html=True
                )
                col3.markdown(f'🌐 `{meta["language"]}`')
                if meta["escalated"]:
                    col4.markdown(
                        '<span class="escalated-badge">🚨 ESCALATED</span>',
                        unsafe_allow_html=True
                    )
                elif meta["llm_called"]:
                    col4.markdown("🤖 LLM used")
                else:
                    col4.markdown("✅ No LLM")

    # Input area
    prefill = st.session_state.pop("prefill", "")
    user_input = st.chat_input(
        "Type your message here... (any language supported)",
    )

    # Handle prefill from sidebar buttons
    if prefill and not user_input:
        user_input = prefill

    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call API
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    data = bridge_chat(
                        message    = user_input,
                        user_id    = user_id,
                        session_id = st.session_state.session_id,
                    )

                    st.session_state.session_id = data.get("session_id")

                    st.markdown(data["response"])

                    meta = {
                        "route_taken": data["route_taken"],
                        "intent":      data.get("intent", ""),
                        "confidence":  data.get("confidence", 1.0),
                        "risk_level":  data["risk_level"],
                        "risk_flags":  data.get("risk_flags", []),
                        "language":    data["language"],
                        "escalated":   data["escalated"],
                        "llm_called":  data["llm_called"],
                        "audit_id":    data.get("audit_id", ""),
                    }

                    col1, col2, col3, col4 = st.columns(4)
                    col1.markdown(
                        f'<span class="route-badge">🔀 {meta["route_taken"]}</span>',
                        unsafe_allow_html=True
                    )
                    risk = meta["risk_level"]
                    col2.markdown(
                        f'<span class="risk-{risk}">⚠️ {risk}</span>',
                        unsafe_allow_html=True
                    )
                    col3.markdown(f'🌐 `{meta["language"]}` | 🎯 `{meta["intent"]}`')
                    if meta["escalated"]:
                        col4.markdown(
                            '<span class="escalated-badge">🚨 ESCALATED</span>',
                            unsafe_allow_html=True
                        )
                    elif meta["llm_called"]:
                        col4.markdown("🤖 LLM used")
                    else:
                        col4.markdown(f"✅ {int(meta['confidence']*100)}% conf")

                    if meta["risk_flags"]:
                        flags_html = " ".join(
                            f'<span class="escalated-badge">{f}</span>'
                            for f in meta["risk_flags"]
                        )
                        st.markdown(f"Risk flags: {flags_html}", unsafe_allow_html=True)
                    if meta["audit_id"]:
                        st.caption(f"Audit ref: {meta['audit_id']}")

                    st.session_state.messages.append({
                        "role":    "assistant",
                        "content": data["response"],
                        "meta":    meta,
                    })

                except requests.exceptions.ConnectionError:
                    st.error("⚠️ Cannot connect to API. Make sure the FastAPI server is running: `uvicorn api.main:app --reload`")
                except Exception as e:
                    st.error(f"⚠️ Error: {e}")

# ── Audit Log tab ─────────────────────────────────────────────────────────────
with tab_audit:
    st.subheader("Recent Decision Audit Log")
    st.caption("Every routing decision is logged for compliance and monitoring.")
    if st.button("🔄 Refresh", key="refresh_audit"):
        st.rerun()
    try:
        logs = bridge_get("/audit/recent?limit=20") or []
        if logs:
            for log in logs:
                with st.expander(
                    f"[{log.get('timestamp','')[:19]}] "
                    f"User: {log.get('user_id','anon')} — "
                    f"Route: {log.get('route_taken','')} — "
                    f"Risk: {log.get('risk_level','')}",
                    expanded=False
                ):
                    st.json(log)
        else:
            st.info("No audit logs yet. Send some messages first.")
    except:
        st.warning("API not reachable. Start the FastAPI server first.")

# ── Escalation Queue tab ──────────────────────────────────────────────────────
with tab_escalations:
    st.subheader("Open Escalation Queue")
    st.caption("Cases flagged for human review.")
    if st.button("🔄 Refresh", key="refresh_esc"):
        st.rerun()
    try:
        tickets = bridge_get("/escalations/open") or []
        if tickets:
            for t in tickets:
                risk = t.get("risk_level", "LOW")
                with st.expander(
                    f"🎫 {t.get('ticket_id','')} — "
                    f"User: {t.get('user_id','anon')} — "
                    f"Reason: {t.get('reason','')} — "
                    f"Risk: {risk}",
                    expanded=risk == "CRITICAL"
                ):
                    st.markdown(f"**Message:** {t.get('message','')}")
                    st.markdown(f"**Status:** {t.get('status','')}")
                    st.markdown(f"**Created:** {t.get('created_at','')}")
        else:
            st.success("✅ No open escalations.")
    except:
        st.warning("API not reachable. Start the FastAPI server first.")

# ── Cost Dashboard tab ────────────────────────────────────────────────────────
with tab_cost:
    st.subheader("LLM Cost Dashboard")
    st.caption(
        "Tracks token usage and estimated cost for every LLM fallback call. "
        "Deterministic routes (safety, services, FAQ, similarity) cost nothing."
    )
    if st.button("🔄 Refresh", key="refresh_cost"):
        st.rerun()
    try:
        data = bridge_get("/cost/summary") or {}

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("LLM Calls",      data.get("total_llm_calls", 0))
        col2.metric("LLM Call Rate",  data.get("llm_call_rate", "0%"))
        col3.metric("Total Cost",     f"${data.get('total_cost_usd', 0):.6f}")
        col4.metric("Avg Latency",    f"{data.get('avg_latency_ms', 0):.0f} ms")
        p95 = data.get("p95_latency_ms")
        col5.metric("p95 Latency",    f"{p95} ms" if p95 is not None else "—")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("Input Tokens",  data.get("total_input_tokens", 0))
        col2.metric("Output Tokens", data.get("total_output_tokens", 0))
        col3.metric("Total Tokens",  data.get("total_tokens", 0))

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        col1.metric("Successful Calls", data.get("successful_calls", 0))
        col2.metric("Failed Calls",     data.get("failed_calls", 0))
        col3.metric("Today Cost",       f"${data.get('today_cost_usd', 0):.6f}")

        st.markdown("---")
        st.subheader("Route Efficiency")
        total = data.get("total_queries_routed", 1)
        llm_n = data.get("total_llm_calls", 0)
        det_n = total - llm_n
        st.markdown(
            f"Out of **{total}** total queries: "
            f"**{det_n}** resolved by deterministic routes (no LLM cost), "
            f"**{llm_n}** required LLM fallback."
        )

        models = data.get("model_breakdown", [])
        if models:
            st.markdown("---")
            st.subheader("Model Breakdown")
            for m in models:
                st.markdown(
                    f"**{m['model']}** — {m['calls']} calls, "
                    f"${m['cost']:.6f} total"
                )

        top = data.get("most_expensive_session")
        if top:
            st.markdown("---")
            st.subheader("Most Expensive Session")
            st.markdown(
                f"Session `{top['session_id']}` — "
                f"${top['session_cost']:.6f}"
            )

    except requests.exceptions.ConnectionError:
        st.warning("API not reachable. Start the FastAPI server first.")
    except Exception as e:
        st.error(f"Error: {e}")


# ── System Metrics tab ────────────────────────────────────────────────────────
with tab_metrics:
    st.subheader("System Metrics")
    st.caption(
        "Operational telemetry: route distribution, safety events, "
        "LLM usage, latency, and system health."
    )
    if st.button("🔄 Refresh", key="refresh_metrics"):
        st.rerun()
    try:
        m = bridge_get("/metrics") or {}

        # ── Top health indicators ─────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Queries",    m.get("total_queries", 0))
        col2.metric("Safety Events",    m.get("safety_events", 0))
        col3.metric("Open Escalations", m.get("open_escalations", 0))
        health = m.get("llm_health", "ok")
        col4.metric("LLM Health", health.upper(),
                    delta=None if health == "ok" else "⚠ degraded",
                    delta_color="normal" if health == "ok" else "inverse")

        st.markdown("---")

        # ── LLM usage ─────────────────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)
        col1.metric("LLM Call Rate",    m.get("llm_call_rate", "0%"))
        col2.metric("LLM Failures",     m.get("llm_failures", 0))
        col3.metric("Total LLM Cost",   f"${m.get('llm_total_cost_usd', 0):.6f}")

        st.markdown("---")

        # ── Route distribution ────────────────────────────────────────────────
        st.subheader("Route Distribution")
        dist = m.get("route_distribution", {})
        total = m.get("total_queries", 1) or 1
        if dist:
            for route, count in sorted(dist.items(), key=lambda x: -x[1]):
                pct = count / total * 100
                st.markdown(f"**{route}** — {count} queries ({pct:.1f}%)")
                st.progress(min(pct / 100, 1.0))
        else:
            st.info("No queries routed yet.")

        st.markdown("---")

        # ── Cache ─────────────────────────────────────────────────────────────
        col1, col2 = st.columns(2)
        col1.metric("Cache Entries",  m.get("cache_entries", 0))
        col2.metric("Cache Hits",     m.get("cache_hits", 0))

    except requests.exceptions.ConnectionError:
        st.warning("API not reachable. Start the FastAPI server first.")
    except Exception as e:
        st.error(f"Error: {e}")
