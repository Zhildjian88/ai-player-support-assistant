"""
response_builder.py
Composes the final response string.

For common routes: returns the response as-is (already in correct language
from pre-translated templates or language-aware services).

For LLM responses: returned directly (Claude handles language natively).

The language signal is available here for any future formatting logic
(e.g. adding localised support contact details).
"""


def build(response: str, lang: str, source: str) -> str:
    """
    Finalises a response for delivery to the player.

    Args:
        response: The raw response string
        lang:     Detected player language code
        source:   The routing source (for future formatting hooks)

    Returns:
        Final response string
    """
    if not response or not response.strip():
        return (
            "I'm sorry, I wasn't able to find an answer to your question. "
            "Please contact our support team via live chat for assistance."
        )

    return response.strip()
