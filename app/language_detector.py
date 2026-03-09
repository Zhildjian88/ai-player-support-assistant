"""
language_detector.py

Detects the language of incoming player messages.
Supports SEA languages: Thai, Indonesian, Vietnamese, Malay, Filipino.
Falls back to English for all other languages.

Uses the lightweight langdetect library (no API cost, runs locally).
"""

try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    DetectorFactory.seed = 42
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False

# Languages we actively translate responses into.
# All others default to English.
SUPPORTED_SEA_LANGUAGES = {
    "th": "Thai",
    "id": "Indonesian",
    "vi": "Vietnamese",
    "ms": "Malay",
    "tl": "Filipino",
}

# langdetect uses 'tl' for Tagalog/Filipino
LANGUAGE_DISPLAY_NAMES = {
    "th": "Thai",
    "id": "Indonesian",
    "vi": "Vietnamese",
    "ms": "Malay",
    "tl": "Filipino",
    "en": "English",
}

DEFAULT_LANGUAGE = "en"


def detect_language(text: str) -> str:
    """
    Detects the language code of the input text.

    Returns a supported SEA language code (th, id, vi, ms, tl)
    or 'en' as the default fallback.

    Args:
        text: Raw player message string.

    Returns:
        ISO 639-1 language code string.
    """
    if not text or len(text.strip()) < 5:
        return DEFAULT_LANGUAGE

    if not _LANGDETECT_AVAILABLE:
        return DEFAULT_LANGUAGE

    try:
        detected = detect(text.strip())

        if detected in SUPPORTED_SEA_LANGUAGES:
            return detected

        return DEFAULT_LANGUAGE

    except Exception:
        return DEFAULT_LANGUAGE


def get_language_name(lang_code: str) -> str:
    """Returns the human-readable name for a language code."""
    return LANGUAGE_DISPLAY_NAMES.get(lang_code, "English")


def is_sea_language(lang_code: str) -> bool:
    """Returns True if the language is a supported SEA language (not English)."""
    return lang_code in SUPPORTED_SEA_LANGUAGES


def get_translation_instruction(lang_code: str) -> str:
    """
    Returns the system prompt instruction to append when a non-English
    language is detected. Used by llm_service.py and response_builder.py.

    Args:
        lang_code: Detected language code.

    Returns:
        Instruction string to include in LLM system prompt.
    """
    if not is_sea_language(lang_code):
        # Explicit English override — prevents prior Malay/Thai/etc context
        # in session history from bleeding into the current English response.
        return (
            "The player's current message is in English. "
            "You MUST respond in English regardless of the language used "
            "in any previous messages in this conversation. "
            "Do not continue in any other language from prior turns."
        )

    lang_name = get_language_name(lang_code)
    return (
        f"The player is communicating in {lang_name}. "
        f"You MUST respond entirely in {lang_name}. "
        f"Do not mix languages. Keep the tone helpful, clear, and professional."
    )


if __name__ == "__main__":
    # Quick smoke test
    test_cases = [
        ("Why is my withdrawal pending?", "en"),
        ("ทำไมการถอนเงินของฉันยังค้างอยู่", "th"),
        ("Kenapa penarikan saya masih pending?", "id"),
        ("Tại sao lệnh rút tiền của tôi vẫn đang chờ xử lý?", "vi"),
        ("Bakit naka-pending pa rin ang aking withdrawal?", "tl"),
    ]

    print("Language Detection Smoke Test\n" + "=" * 40)
    for text, expected in test_cases:
        result = detect_language(text)
        status = "✓" if result == expected else f"✗ (expected {expected})"
        print(f"[{result}] {status} — {text[:50]}")
