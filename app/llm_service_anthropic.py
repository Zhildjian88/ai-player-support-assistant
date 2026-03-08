"""
llm_service_anthropic.py  —  Anthropic Claude Haiku implementation
Alternative LLM provider. Used before switching to Groq as the default demo provider.

To switch back to Anthropic:
    1. Set ANTHROPIC_API_KEY in .env
    2. pip install anthropic
    3. Replace app/llm_service.py with this file

The project originally used Anthropic Claude Haiku during development and testing.
Groq (llama-3.1-8b-instant) was adopted as the default demo provider due to its
free tier and comparable quality for support chat queries at the 5% LLM fallback rate.

Interface contract (identical to llm_service.py):
    call() returns: response, model, input_tokens, output_tokens, llm_success, latency_ms
"""

import os
import time
from pathlib import Path

SYSTEM_PROMPT = """You are a helpful and professional player support assistant
for a licensed online casino and sportsbook operator serving Southeast Asia,
Australia, and the United Kingdom.

Your responsibilities:
- Answer player questions clearly and accurately about accounts, payments,
  promotions, game rules, and general platform queries
- Be respectful, empathetic, and concise
- Never invent account balances, payment statuses, or promotion terms
- Never advise on how to beat, exploit, or cheat any game or system
- If a player seems distressed or mentions gambling problems, respond with
  care and refer them to responsible gaming support

Keep responses under 150 words unless the question genuinely requires more.
"""

SAFE_FALLBACK = (
    "I'm sorry, I wasn't able to process your request right now. "
    "Please contact our support team directly via live chat for immediate assistance."
)

MODEL_ID = "claude-haiku-4-5-20251001"


def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass


def _build_account_context(user_id: str) -> str:
    try:
        from app.db_init import get_connection
        conn = get_connection()
        row  = conn.execute(
            "SELECT account_status, kyc_status, vip_tier FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        conn.close()
        if row:
            return (
                f"\nPlayer context: account_status={row['account_status']}, "
                f"kyc_status={row['kyc_status']}, vip_tier={row['vip_tier']}"
            )
    except Exception:
        pass
    return ""


def call(
    message:          str,
    user_id:          str | None = None,
    lang_instruction: str = "",
    session_context:  list[dict] | None = None,
) -> dict:
    start = time.monotonic()
    _load_env()

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _failure("No ANTHROPIC_API_KEY configured in .env", start)

    system = SYSTEM_PROMPT
    if lang_instruction:
        system += f"\n\n{lang_instruction}"
    if user_id:
        system += _build_account_context(user_id)

    messages = list(session_context or [])
    messages.append({"role": "user", "content": message})

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model      = os.getenv("LLM_MODEL", MODEL_ID),
            max_tokens = int(os.getenv("LLM_MAX_TOKENS", "512")),
            system     = system,
            messages   = messages,
        )

        latency_ms    = int((time.monotonic() - start) * 1000)
        response_text = response.content[0].text
        usage         = response.usage

        return {
            "response":      response_text,
            "model":         response.model,
            "input_tokens":  usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "llm_success":   True,
            "latency_ms":    latency_ms,
        }

    except Exception as e:
        print(f"[llm_service] Anthropic API error: {type(e).__name__}: {e}")
        return _failure(str(e), start)


def _failure(reason: str, start: float) -> dict:
    latency_ms = int((time.monotonic() - start) * 1000)
    return {
        "response":      SAFE_FALLBACK,
        "model":         "none",
        "input_tokens":  0,
        "output_tokens": 0,
        "llm_success":   False,
        "latency_ms":    latency_ms,
    }
