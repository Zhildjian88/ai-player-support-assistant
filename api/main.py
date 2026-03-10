"""
main.py
FastAPI gateway for the AI Player Support Assistant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.router import process_message

app = FastAPI(
    title="AI Player Support Assistant",
    description=(
        "Cost-aware, risk-aware player support automation for a mixed iGaming operator. "
        "Routes queries through policy guardrails, safety detectors, dynamic data services, "
        "semantic retrieval, and LLM fallback — in that order."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://zhildjian88.github.io",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https://.*\.github\.io",
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id:  Optional[str] = None
    message:  str
    session_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id":    "U1001",
                "message":    "Why is my withdrawal still pending?",
                "session_id": "sess_abc123"
            }
        }


class ChatResponse(BaseModel):
    response:    str
    language:    str
    route_taken: str
    source:      str
    intent:      str
    confidence:  float
    risk_level:  str
    risk_flags:  list[str]
    escalated:   bool
    llm_called:  bool
    llm_model:   Optional[str] = None
    llm_success: Optional[bool] = None
    latency_ms:  Optional[int] = None
    audit_id:    Optional[str] = None
    session_id:  Optional[str] = None


@app.get("/", tags=["health"])
def root():
    return {
        "service": "AI Player Support Assistant",
        "status":  "online",
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
def health():
    from app.language_detector import detect_language
    from app.distress_detector import check as distress_check
    msg = "我再也无法忍受了，我想结束我的生命。"
    lang = detect_language(msg)
    distress = distress_check(msg, lang)
    route_result = process_message(msg, user_id="U1001")
    return {
        "status": "ok",
        "debug_lang": lang,
        "debug_signal": distress["signal"],
        "debug_subtype": distress["subtype"],
        "debug_distress_response": distress["response"][:60],
        "pipeline_route": route_result["route_taken"],
        "pipeline_lang": route_result["language"],
        "pipeline_response": route_result["response"][:80],
    }


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = process_message(
        message=request.message.strip(),
        user_id=request.user_id,
        session_id=request.session_id,
    )

    return ChatResponse(**result)


@app.get("/audit/recent", tags=["audit"])
def recent_audit_logs(limit: int = 20):
    from app.db_init import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/cost/summary", tags=["cost"])
def cost_summary():
    from app.cost_service import get_summary
    return get_summary()


@app.get("/metrics", tags=["metrics"])
def metrics():
    from app.metrics_service import get_metrics
    return get_metrics()


@app.get("/search/stats", tags=["search"])
def search_stats():
    from app.similarity_service import get_index_stats
    return get_index_stats()


@app.get("/escalations/open", tags=["escalation"])
def open_escalations():
    from app.db_init import get_connection
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM escalation_queue WHERE status='open' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
