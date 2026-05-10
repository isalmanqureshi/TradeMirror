from __future__ import annotations

ADVICE_PATTERNS = (
    "should i buy",
    "should i sell",
    "should i enter",
    "should i short",
    "what trade should i take",
)

BANNED_PHRASES = (
    "you should buy",
    "you should sell",
    "take the trade",
    "enter now",
    "short now",
    "go long",
)


def is_direct_advice_request(message: str) -> bool:
    text = message.lower()
    return any(pattern in text for pattern in ADVICE_PATTERNS)


def safe_advice_refusal() -> str:
    return (
        "I can analyze your historical trading data and risk patterns, but I cannot "
        "tell you whether to buy, sell, short, enter, exit, or use leverage."
    )


def sanitize_answer(answer: str) -> str:
    sanitized = answer
    for phrase in BANNED_PHRASES:
        sanitized = sanitized.replace(phrase, "consider reviewing")
    return sanitized
