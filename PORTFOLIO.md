# AI Player Support Assistant — Portfolio Summary

**Safety-first AI support routing system resolving 90.8% of queries without LLM usage while maintaining 85% safety detection accuracy on a synthetic evaluation set.**

Built by SWK · March 2026  
Platform Integrity & Risk Lead | MSc AI/ML (Distinction)  
SiDO Strategies — AI Governance & Risk Advisory

---

## 🚀 Live Demo

**→ [https://Zhildjian88.github.io/ai-player-support-assistant/](https://Zhildjian88.github.io/ai-player-support-assistant/)**

Open the link and interact directly — no account, no setup, no local install needed.

The player UI runs on GitHub Pages (static HTML). Chat messages are routed through a FastAPI backend on Render, which runs the full 14-step router pipeline including LLM fallback via Groq.

---

## Problem

Online gaming platforms handle high volumes of player support queries across multiple languages and time zones. These queries range from routine account and payment questions to urgent safety signals such as distress, problem gambling, and account fraud. A single LLM handling all queries creates three risks:

- **Safety risk** — a generative model may not reliably detect or escalate crisis signals
- **Cost risk** — LLM calls are expensive; most queries are answerable deterministically
- **Reliability risk** — generative responses are non-deterministic and hard to audit

---

## Approach

A 14-step priority router that processes every message through layered checks before invoking an LLM. Safety always executes first. The LLM is the final fallback, not the primary decision-maker.

---

## Architecture

Six layers, executed in strict order:

| Layer | Components | Purpose |
|-------|-----------|---------|
| Safety | Policy guardrail, distress, RG, fraud, circumvention | Block, escalate, protect |
| Operational | Account, payment, promotions services | Real-time DB lookups |
| Knowledge | Game rules, FAQ keyword match | Deterministic answers |
| Cache | Exact-match answer store | Zero-cost repeat queries |
| Semantic | FAISS cosine retrieval | Fuzzy knowledge matching |
| Generative | Groq LLM fallback (Anthropic tested as alternative) | Novel and ambiguous queries |

Every response carries a structured decision trace recording route taken, risk level, risk flags, escalation status, LLM usage, and audit ID. All traces are persisted to SQLite.

---

## Deployment Stack

| Component | Technology | Hosting |
|-----------|-----------|---------|
| Player UI | Static HTML + React (Babel CDN) | GitHub Pages — free, always on |
| FastAPI backend | Python 3.11, uvicorn | Render free tier |
| LLM fallback | Groq `llama-3.1-8b-instant` | Groq cloud (free tier) |
| Ops console | Streamlit | Local only |
| Database | SQLite | Render ephemeral (demo) |

No infrastructure costs for portfolio use. Every `git push` to `main` redeploys both the frontend (GitHub Pages) and backend (Render) automatically.

---

## Key Results

Evaluated on 120 synthetic player support queries across all route categories.

| Metric | Result |
|--------|--------|
| Overall routing accuracy | 86.7% |
| Safety signal detection accuracy | 85.0% |
| Operational services accuracy | 97.7% |
| Knowledge route accuracy | 88.9% |
| Deterministic route resolution | 90.8% |
| LLM fallback rate | 5.0% |
| Average latency (warmed) | 15 ms |
| p95 latency | 30 ms |
| Test coverage | 91 tests, 100% pass |

Most queries (95%) were resolved through deterministic routing or semantic retrieval; only 5% required LLM fallback.

### Accuracy by Bucket

| Bucket | Accuracy |
|--------|----------|
| Operational services | 97.7% |
| Knowledge routes | 88.9% |
| Safety signals | 85.0% |
| LLM fallback label¹ | 40.0% |

¹ The 40% figure for LLM fallback label reflects label-mismatch in the evaluation set — many queries labelled `llm_fallback` were correctly resolved by semantic retrieval or FAQ routes, producing a good answer through a different route than the label specified.

### Critical Safety Miss Count

Of 40 safety-labelled queries, 6 were misrouted. Misses fall into two categories: phrase coverage gaps in keyword detectors (addressable by expanding signal lists), and ambiguous queries where the actual route still produces a safe response.

---

## Technical Decisions

**Why a priority router instead of an LLM classifier?**  
Deterministic routing guarantees that safety signals cannot be overridden by a generative response. An LLM classifier introduces probabilistic uncertainty precisely where reliability is most critical.

**Why GitHub Pages + Render instead of Streamlit Cloud?**  
Streamlit's widget rendering model injects container chrome around every element, making pixel-accurate UI design impossible. Deploying the player UI as a static HTML file gives exact control over every visual detail, while Render hosts the full backend pipeline including LLM fallback — with no compromise on functionality.

**Why FAISS IndexFlatIP over IVF or HNSW?**  
The corpus is under 1,000 documents. Exact search is simpler, has no approximation error, and eliminates index-tuning overhead at this scale.

**Why a dual-backend retrieval design?**  
The neural embedding backend requires a model download (~420 MB). The TF-IDF lexical backend uses the same FAISS interface with no model loading — making the system runnable on Render's free tier without structural changes to the router.

**Why bounded session context?**  
Context is capped at five prior turn pairs. This provides enough conversational continuity for support follow-ups while keeping token costs predictable.

---

## Known Limitations

- Uses synthetic data rather than real player interactions
- Retrieval corpus is small — 57 anchors across FAQ, game rules, and approved answers
- Safety detectors use keyword matching rather than trained classifiers
- LLM fallback prompt is static rather than dynamically tuned per query type
- No authentication or rate limiting on the API
- No PII redaction before LLM calls

---

## What a Production Version Would Add

1. **Human-labelled training data** — replace synthetic queries with real support tickets
2. **Confidence thresholds** — route borderline similarity matches to human review
3. **Feedback loop** — reviewer decisions update the gold evaluation dataset
4. **PII redaction** — strip account numbers, card details, and contact information before any LLM call
5. **Rate limiting and authentication** — API key validation and per-session rate limits
6. **A/B testing framework** — measure response quality across router versions
7. **Alerting** — trigger ops notifications when distress or fraud escalation rates spike
8. **PostgreSQL** — replace SQLite for concurrent multi-replica production use

---

## 🎤 Talking Points

**"Walk me through your project."**

I built a safety-first AI support routing system for an online gaming platform. The key design decision was prioritising deterministic safety and operational routes before any semantic or generative AI. The router checks policy violations, distress signals, responsible gaming signals, and fraud indicators first, then live operational services, then semantic retrieval, with the LLM used strictly as a final fallback. The system is fully deployed — the player UI is live on GitHub Pages, the backend runs on Render, and hirers can interact with it directly at the link in this document.

**"Why not use an LLM for everything?"**

Generative models cannot guarantee deterministic behaviour, and they don't have access to operational data like account state or payment status. This system uses layered routing — deterministic safety checks, structured services, semantic retrieval, and only then an LLM fallback — giving you reliability where it matters and flexibility where determinism isn't required.

**"How did you control cost and latency?"**

The router resolves over 90% of queries without invoking the model at all. For queries that do reach the LLM, a cost instrumentation layer records token usage, estimated USD cost, model name, success state, and latency per call — making LLM usage visible and auditable rather than a black box operational cost.

**"How would you extend this to production?"**

Replace synthetic data with human-labelled production tickets; add confidence thresholds to route borderline cases to human review; build a feedback loop where reviewer decisions update the evaluation dataset; and add PII redaction before any content reaches the LLM. The architecture already supports all of these.

---

## 📝 License

© 2026 SiDO Strategies  
Published for portfolio and evaluation purposes.  
The code may be viewed and referenced for learning and evaluation.  
Commercial reuse or redistribution without written permission is prohibited.  
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

Built by SWK · March 2026 · Platform Integrity & Risk Lead | MSc AI/ML (Distinction)  
SiDO Strategies — AI Governance & Risk Advisory
