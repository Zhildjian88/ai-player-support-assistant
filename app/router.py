"""
router.py
Decision Router — the brain of the AI Player Support Assistant.

Routing priority (safety-first, cheapest before expensive):
    1.  Policy guardrail       — block prohibited queries immediately
    2.  Distress detection     — crisis / self-harm / physical danger → CRITICAL escalation
    3.  Responsible gaming     — gambling harm signals → RG support + escalation
    4.  Fraud / security       — unauthorised access → security escalation
    5.  Circumvention          — limit removal / exclusion bypass / multi-accounting → HIGH escalation
    6.  Account service        — account / KYC status lookup
    7.  Payment service        — withdrawal / deposit status lookup
    8.  Promotions service     — active promotions lookup
    9.  Game rules service     — static game knowledge
   10.  FAQ service            — static support knowledge
   11.  Exact cache hit        — previously answered identical question
   12.  Semantic similarity    — multilingual FAISS match (approved answers + FAQ)
   13.  LLM fallback           — novel, ambiguous, or multi-intent queries

Design principles applied:
    - Safety layers (1–4) always short-circuit before any support answer is returned.
    - Operational services (5–7) checked before knowledge retrieval (8–11).
    - LLM is called only when all cheaper routes are exhausted.
    - Multilingual embeddings (paraphrase-multilingual-MiniLM-L12-v2) support
      cross-language similarity search without a translation step.
    - Language signal passes through to response builder for template selection.
    - Every decision produces a structured trace for audit and compliance.
"""

import uuid
from datetime import datetime
from app.language_detector import detect_language, get_translation_instruction

# ── Lazy imports (heavy modules loaded on first use) ──────────────────────────
_modules_loaded = False
_policy = _distress = _rg = _fraud = _circumvention = None
_account = _payment = _promo = None
_game = _faq = _cache = _similarity = None
_llm = _builder = _audit = _escalation = None
_cost = _context = _intent_clf = None


def _load():
    global _modules_loaded
    global _policy, _distress, _rg, _fraud, _circumvention
    global _account, _payment, _promo
    global _game, _faq, _cache, _similarity
    global _llm, _builder, _audit, _escalation
    global _cost, _context, _intent_clf

    if _modules_loaded:
        return

    from app import (
        policy_guardrail      as _p,
        distress_detector     as _d,
        rg_detector           as _rg_m,
        fraud_detector        as _f,
        circumvention_detector as _cv,
        account_service    as _acc,
        payment_service    as _pay,
        promotions_service as _pro,
        game_rules_service as _gm,
        faq_service        as _fq,
        cache_service      as _ch,
        similarity_service as _sim,
        llm_service        as _ll,
        response_builder   as _rb,
        audit_logger       as _al,
        escalation_service as _es,
        cost_service       as _cs,
        context_service    as _ctx,
        intent_classifier  as _ic,
    )
    _policy         = _p
    _distress       = _d
    _rg             = _rg_m
    _fraud          = _f
    _circumvention  = _cv
    _account    = _acc
    _payment    = _pay
    _promo      = _pro
    _game       = _gm
    _faq        = _fq
    _cache      = _ch
    _similarity = _sim
    _llm        = _ll
    _builder    = _rb
    _audit      = _al
    _escalation = _es
    _cost       = _cs
    _context    = _ctx
    _intent_clf = _ic
    _modules_loaded = True


# ── Intent mapping ────────────────────────────────────────────────────────────
ROUTE_TO_INTENT = {
    "policy_guardrail":       "prohibited_query",
    "distress_detector":      "player_distress",
    "rg_detector":            "responsible_gaming",
    "fraud_detector":         "security_incident",
    "circumvention_detector": "limit_circumvention",
    "account_service":    "account_status",
    "payment_service":    "payment_status",
    "promotions_service": "promotions_query",
    "game_rules_service": "game_rules_query",
    "faq_service":        "general_support",
    "cache":              "cached_response",
    "similarity_service": "semantic_match",
    "llm_fallback":       "novel_query",
}

# ── Risk flag mapping ─────────────────────────────────────────────────────────
ROUTE_TO_FLAGS = {
    "policy_guardrail":       ["POLICY_VIOLATION"],
    "distress_detector":      ["DISTRESS", "ESCALATED"],
    "rg_detector":            ["RG_SIGNAL", "ESCALATED"],
    "fraud_detector":         ["SECURITY", "ESCALATED"],
    "circumvention_detector": ["CIRCUMVENTION", "ESCALATED"],
    "account_service":    [],
    "payment_service":    [],
    "promotions_service": [],
    "game_rules_service": [],
    "faq_service":        [],
    "cache":              [],
    "similarity_service": [],
    "llm_fallback":       [],
}


# ── Main entry point ──────────────────────────────────────────────────────────

def process_message(
    message:    str,
    user_id:    str | None = None,
    session_id: str | None = None,
) -> dict:
    """
    Routes a player message through the full decision pipeline.

    Returns a structured decision trace dict matching ChatResponse:
        response    : str       — final player-facing response
        language    : str       — detected language code
        route_taken : str       — winning route
        source      : str       — alias for route_taken
        intent      : str       — semantic intent label
        confidence  : float     — routing confidence (0.0–1.0)
        risk_level  : str       — LOW / MEDIUM / HIGH / CRITICAL
        risk_flags  : list[str] — active risk signal labels
        escalated   : bool
        llm_called  : bool
        audit_id    : str       — audit log reference
        session_id  : str
    """
    _load()

    session_id = session_id or str(uuid.uuid4())
    audit_id   = f"AUD-{uuid.uuid4().hex[:10].upper()}"
    lang       = detect_language(message)
    escalated  = False
    llm_called = False
    risk_level = "LOW"
    confidence = 1.0   # Rule-based routes are deterministic → confidence = 1.0

    # ── 0. Quick action token resolution ────────────────────────────────────
    # action:* tokens are sent by the player UI quick action buttons.
    # They bypass NLP and route deterministically to the correct service.
    _ACTION_MAP = {
        "action:balance":     ("account_service",   "balance_inquiry"),
        "action:withdrawal":  ("payment_service",   "withdrawal_status"),
        "action:promotions":  ("promotions_service","promotions_inquiry"),
        "action:kyc":         ("account_service",   "kyc_status"),
        "action:rules":       ("game_rules_service", "game_rules_inquiry"),
        "action:rg":          ("rg_detector",        "rg_support"),
    }
    _ACTION_LABELS = {
        "action:balance":    "Player checked account balance",
        "action:withdrawal": "Player checked withdrawal status",
        "action:promotions": "Player checked active promotions",
        "action:kyc":        "Player checked KYC status",
        "action:rules":      "Player checked game rules",
        "action:rg":         "Player requested Responsible Gaming support",
    }
    _msg_stripped = message.strip().lower()
    if _msg_stripped in _ACTION_MAP:
        _route, _intent = _ACTION_MAP[_msg_stripped]
        _audit_message = _ACTION_LABELS.get(_msg_stripped, message)
        if _msg_stripped == "action:rg":
            rg_i18n = _rg.SAFE_RESPONSE_I18N.get(lang, _rg.SAFE_RESPONSE) if hasattr(_rg, "SAFE_RESPONSE_I18N") else _rg.SAFE_RESPONSE
            response   = _builder.build(rg_i18n, lang, _route)
            risk_level = "HIGH"
            escalated  = True
            _escalation.create(session_id, user_id, "Player requested Responsible Gaming support", "rg_quick_action", risk_level)
        elif _msg_stripped == "action:balance":
            acct     = _account.lookup("my balance", user_id) if user_id else {}
            response = _builder.build(acct.get("response", "Your balance is available in the account section."), lang, _route)
        elif _msg_stripped == "action:withdrawal":
            pay      = _payment.lookup("withdrawal", user_id) if user_id else {}
            response = _builder.build(pay.get("response", "No pending withdrawals found on your account."), lang, _route)
        elif _msg_stripped == "action:promotions":
            promo    = _promo.lookup("promotions", user_id) if user_id else {}
            response = _builder.build(promo.get("response", "No active promotions available at this time."), lang, _route)
        elif _msg_stripped == "action:kyc":
            acct     = _account.lookup("my kyc status", user_id) if user_id else {}
            response = _builder.build(acct.get("response", "Your KYC status is available in your account settings."), lang, _route)
        elif _msg_stripped == "action:rules":
            game_directory = (
                "Here are the games available at SiDOBet. Ask me about any game to see its full rules:\n\n"
                "\U0001f0cf **Blackjack** — Beat the dealer to 21 without going bust\n"
                "\U0001f3b0 **Slots** — Spin to match symbols across paylines\n"
                "\U0001f3a1 **Roulette** — Bet on where the ball lands on the wheel\n"
                "\U0001f004 **Baccarat** — Back Player, Banker, or Tie\n"
                "\u2660\ufe0f **Poker** — Three Card Poker and more\n"
                "\u26bd **Sports Betting** — Pre-match and live betting markets\n\n"
                "Just type the name of a game (e.g. \"How do I play Blackjack?\") and I\'ll show you the rules."
            )
            response = _builder.build(game_directory, lang, _route)
        else:
            response = _builder.build("I can help you with that. Please contact support for details.", lang, _route)
        _log(audit_id, session_id, user_id, _audit_message, _route, risk_level,
             False, _msg_stripped == "action:rg", False, escalated, response)
        return _pack(response, lang, _route, _intent, confidence, risk_level,
                     ROUTE_TO_FLAGS.get(_route, []), escalated, llm_called,
                     audit_id, session_id)

    # ── 1. Policy hard stops (injection / harmful / prohibited gambling) ──────
    # Out-of-scope check is intentionally deferred until after distress/RG
    # so mixed messages like "I'm depressed, capital of France?" still trigger
    # the distress handler rather than being dismissed as off-topic.
    policy_result = _policy.check_hard_stops(message)
    if policy_result["blocked"]:
        route      = "policy_guardrail"
        risk_level = "MEDIUM"
        response   = _builder.build(policy_result["response"], lang, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 2. Intent classifier (LLM-based, language-agnostic) ──────────────────
    # Runs only when keyword guardrail did NOT fire — catches novel phrasings,
    # unsupported languages, and mixed-language attacks that keywords miss.
    # Fails open (returns support_query) on API error so players are never
    # blocked by a classifier outage — keyword guardrails remain the safety net.
    clf_result = _intent_clf.classify(message, lang)
    clf_intent = clf_result.get("intent", "support_query")

    if clf_intent == "injection":
        route      = "policy_guardrail"
        risk_level = "MEDIUM"
        from app.policy_guardrail import INJECTION_RESPONSE
        response   = _builder.build(INJECTION_RESPONSE, lang, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     clf_result.get("confidence", 0.9), risk_level,
                     ROUTE_TO_FLAGS[route], escalated, llm_called,
                     audit_id, session_id)

    if clf_intent == "distress":
        # Hand off to distress detector for proper i18n response + escalation
        distress_result = _distress.check(message, lang)
        if not distress_result["signal"]:
            # Classifier caught it but keyword distress missed — use safe fallback
            distress_result = _distress.check("I want to hurt myself", lang)
        route      = "distress_detector"
        risk_level = "CRITICAL"
        escalated  = True
        response   = _builder.build(distress_result["response"], lang, route)
        _escalation.create(session_id, user_id, message, "distress_signal", risk_level)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             True, False, False, True, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     clf_result.get("confidence", 0.9), risk_level,
                     ROUTE_TO_FLAGS[route], escalated, llm_called,
                     audit_id, session_id)

    if clf_intent == "out_of_scope":
        from app.policy_guardrail import OUT_OF_SCOPE_RESPONSE
        route      = "policy_guardrail"
        risk_level = "LOW"
        response   = _builder.build(OUT_OF_SCOPE_RESPONSE, lang, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     clf_result.get("confidence", 0.9), risk_level,
                     ROUTE_TO_FLAGS[route], escalated, llm_called,
                     audit_id, session_id)

    # clf_intent == "support_query" — continue through normal pipeline
    # ── 3. Distress detection (keyword-based, fast path) ─────────────────────
    distress_result = _distress.check(message, lang)
    if distress_result["signal"]:
        route      = "distress_detector"
        risk_level = "CRITICAL"
        escalated  = True
        response   = _builder.build(distress_result["response"], lang, route)
        _escalation.create(session_id, user_id, message, "distress_signal", risk_level)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             True, False, False, True, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 4. Responsible gaming detection ──────────────────────────────────────
    rg_result = _rg.check_with_lang(message, lang) if hasattr(_rg, "check_with_lang") else _rg.check(message)
    if rg_result["signal"]:
        route      = "rg_detector"
        risk_level = "HIGH"
        escalated  = True
        response   = _builder.build(rg_result["response"], lang, route)
        _escalation.create(session_id, user_id, message, "rg_signal", risk_level)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, True, False, True, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 4. Fraud / security detection ────────────────────────────────────────
    fraud_result = _fraud.check(message)
    if fraud_result["signal"]:
        route      = "fraud_detector"
        risk_level = "HIGH"
        escalated  = True
        response   = _builder.build(fraud_result["response"], lang, route)
        _escalation.create(session_id, user_id, message, "fraud_signal", risk_level)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, True, True, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 5. Circumvention detection ────────────────────────────────────────────
    cv_result = _circumvention.check(message)
    if cv_result["signal"]:
        route      = "circumvention_detector"
        risk_level = "HIGH"
        escalated  = True
        response   = _builder.build(cv_result["response"], lang, route)
        _escalation.create(session_id, user_id, message,
                           f"circumvention_{cv_result['subtype']}", risk_level)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, True, True, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 5b. Out-of-scope check ────────────────────────────────────────────────
    # Runs here — AFTER distress/RG/fraud — so safety signals always fire first.
    # A message like "I'm depressed, capital of France?" will have already been
    # caught by distress above; only genuinely off-topic messages reach this point.
    oos_result = _policy.check_out_of_scope(message)
    if oos_result["blocked"]:
        route      = "policy_guardrail"
        risk_level = "LOW"
        response   = _builder.build(oos_result["response"], lang, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 6. Account service ────────────────────────────────────────────────────
    if user_id:
        account_result = _account.lookup(message, user_id)
        if account_result["matched"]:
            route    = "account_service"
            response = _builder.build(account_result["response"], lang, route)
            _log(audit_id, session_id, user_id, message, route, risk_level,
                 False, False, False, False, response)
            return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                         confidence, risk_level, ROUTE_TO_FLAGS[route],
                         escalated, llm_called, audit_id, session_id)

    # ── 7. Payment service ────────────────────────────────────────────────────
    if user_id:
        payment_result = _payment.lookup(message, user_id)
        if payment_result["matched"]:
            route    = "payment_service"
            response = _builder.build(payment_result["response"], lang, route)
            _log(audit_id, session_id, user_id, message, route, risk_level,
                 False, False, False, False, response)
            return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                         confidence, risk_level, ROUTE_TO_FLAGS[route],
                         escalated, llm_called, audit_id, session_id)

    # ── 8. Promotions service ─────────────────────────────────────────────────
    promo_result = _promo.lookup(message, user_id)
    if promo_result["matched"]:
        route    = "promotions_service"
        response = _builder.build(promo_result["response"], lang, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 9. Game rules service ─────────────────────────────────────────────────
    game_result = _game.lookup(message)
    if game_result["matched"]:
        route    = "game_rules_service"
        response = _builder.build(game_result["response"], lang, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 10. FAQ service ────────────────────────────────────────────────────────
    faq_result = _faq.lookup(message)
    if faq_result["matched"]:
        route    = "faq_service"
        response = _builder.build(faq_result["response"], lang, route)
        _cache.store(message, response, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 11. Exact cache lookup ────────────────────────────────────────────────
    cache_result = _cache.lookup(message)
    if cache_result["hit"]:
        route    = "cache"
        response = _builder.build(cache_result["response"], lang, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        return _pack(response, lang, route, ROUTE_TO_INTENT[route],
                     confidence, risk_level, ROUTE_TO_FLAGS[route],
                     escalated, llm_called, audit_id, session_id)

    # ── 12. Semantic similarity (FAISS + multilingual embeddings) ─────────────
    similarity_result = _similarity.search(message, lang)
    if similarity_result["matched"]:
        route       = "similarity_service"
        confidence  = round(float(similarity_result.get("score", 0.85)), 4)
        response    = _builder.build(similarity_result["response"], lang, route)
        _cache.store(message, response, route)
        _log(audit_id, session_id, user_id, message, route, risk_level,
             False, False, False, False, response)
        result = _pack(response, lang, route, ROUTE_TO_INTENT[route],
                       confidence, risk_level, ROUTE_TO_FLAGS[route],
                       escalated, llm_called, audit_id, session_id)
        # Attach similarity metadata for audit traceability
        result["similarity_meta"] = {
            "source_id":   similarity_result.get("source_id", ""),
            "source_type": similarity_result.get("source_type", ""),
            "backend":     similarity_result.get("backend", ""),
            "threshold":   similarity_result.get("threshold", 0),
            "score":       confidence,
        }
        return result

    # ── 13. LLM fallback ──────────────────────────────────────────────────────
    llm_called       = True
    confidence       = 0.5
    lang_instruction = get_translation_instruction(lang)
    session_context  = _context.get_context(session_id)

    llm_result = _llm.call(
        message          = message,
        user_id          = user_id,
        lang_instruction = lang_instruction,
        session_context  = session_context,
    )

    route      = "llm_fallback"
    response   = llm_result["response"]
    llm_model  = llm_result["model"]
    llm_success= llm_result["llm_success"]
    latency_ms = llm_result["latency_ms"]

    # Record cost — even failed calls are recorded (tokens=0, success=False)
    _cost.record(
        session_id    = session_id,
        user_id       = user_id,
        model         = llm_model,
        input_tokens  = llm_result["input_tokens"],
        output_tokens = llm_result["output_tokens"],
        llm_success   = llm_success,
        latency_ms    = latency_ms,
    )

    # Store turn in session context (only on success)
    if llm_success:
        _context.store_turn(session_id, message, response)
        _cache.store(message, response, route)

    _log(audit_id, session_id, user_id, message, route, risk_level,
         False, False, False, False, response, llm_called=True)

    result = _pack(response, lang, route, ROUTE_TO_INTENT[route],
                   confidence, risk_level, ROUTE_TO_FLAGS[route],
                   escalated, llm_called, audit_id, session_id)
    result["llm_model"]   = llm_model
    result["llm_success"]  = llm_success
    result["latency_ms"]   = latency_ms
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pack(response, lang, route, intent, confidence,
          risk_level, risk_flags, escalated, llm_called,
          audit_id, session_id) -> dict:
    return {
        "response":    response,
        "language":    lang,
        "route_taken": route,
        "source":      route,
        "intent":      intent,
        "confidence":  confidence,
        "risk_level":  risk_level,
        "risk_flags":  risk_flags,
        "escalated":   escalated,
        "llm_called":  llm_called,
        "audit_id":    audit_id,
        "session_id":  session_id,
    }


def _log(audit_id, session_id, user_id, message, route,
         risk_level, distress, rg, fraud, escalated, response,
         llm_called=False):
    _audit.log(
        session_id      = session_id,
        user_id         = user_id,
        message         = message,
        route_taken     = route,
        risk_level      = risk_level,
        distress_signal = distress,
        rg_signal       = rg,
        fraud_signal    = fraud,
        escalated       = escalated,
        response        = response,
        llm_called      = llm_called,
    )
