from __future__ import annotations

from app.services.chat.types import IntentClassification

INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "performance_summary": (
        "performance",
        "summary",
        "how did i do",
        "how did my strategy perform",
        "how did my trading perform",
        "how did my trades perform",
        "trading performance",
        "perform",
        "strategy perform",
        "strategy performance",
        "pnl",
        "win rate",
        "profit factor",
        "underperform",
        "performed",
    ),
    "regime_analysis": ("regime", "volatility", "trend", "market condition", "high vol", "low vol", "ranging"),
    "execution_quality": ("slippage", "fees", "execution", "order type", "fills"),
    "risk_drift": ("risk", "oversized", "position size", "planned risk", "actual risk"),
    "edge_decay": ("edge", "decay", "getting worse", "rolling", "deteriorating"),
    "backtest_live_comparison": ("backtest", "live", "drift", "drifting", "valid", "still working"),
    "trade_lookup": ("show trades", "recent trades", "losing trades", "winning trades", "worst trades", "best trades"),
    "journal_lookup": ("journal", "mistake", "emotion", "notes", "review"),
    "trade_context_lookup": ("context", "atr", "vix", "macro", "event", "session"),
}

PRIORITY: list[str] = [
    "backtest_live_comparison",
    "performance_summary",
    "regime_analysis",
    "execution_quality",
    "risk_drift",
    "edge_decay",
    "trade_lookup",
    "journal_lookup",
    "trade_context_lookup",
]

RISK_TERMS = ("risk", "planned risk", "actual risk", "position size", "oversized")
RISK_DRIFT_TERMS = ("drift", "drifting", "changed", "change", "over time")


def classify_intent(message: str) -> IntentClassification:
    normalized = message.lower().strip()

    if any(term in normalized for term in RISK_TERMS) and any(term in normalized for term in RISK_DRIFT_TERMS):
        return IntentClassification("risk_drift", [], 0.95, "matched risk terms with drift/change terms")

    matches: dict[str, list[str]] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        found = [keyword for keyword in keywords if keyword in normalized]
        if found:
            matches[intent] = found

    if not matches:
        return IntentClassification("unknown", [], 0.0, "no keyword matches")

    ranked = sorted(matches, key=lambda key: (-len(matches[key]), PRIORITY.index(key)))
    primary = ranked[0]
    secondary = [intent for intent in ranked[1:] if intent != primary]
    confidence = min(1.0, 0.5 + (0.1 * len(matches[primary])))
    reason = ", ".join(f"{intent}: {matches[intent]}" for intent in ranked)
    return IntentClassification(primary, secondary, confidence, f"matched keywords -> {reason}")
