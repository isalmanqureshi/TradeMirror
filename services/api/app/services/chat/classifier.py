from __future__ import annotations

from app.services.chat.types import IntentClassification

INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "performance_summary": ("performance", "how did my", "win rate", "summarize", "pnl", "profit factor"),
    "regime_analysis": ("regime", "volatility", "trend", "market condition", "high vol", "low vol"),
    "execution_quality": ("slippage", "fees", "execution", "order type", "fills", "execution cost"),
    "risk_drift": ("risk drift", "exceed planned risk", "oversized", "actual risk", "planned risk"),
    "edge_decay": ("edge decay", "rolling expectancy", "deteriorating", "getting worse"),
    "backtest_live_comparison": ("backtest", "live", "drifting", "still valid", "compare live"),
    "trade_lookup": ("show trades", "recent trades", "losing trades", "winning trades", "worst trades", "best trades"),
    "journal_lookup": ("journal", "mistake", "emotion", "notes", "revenge", "fomo"),
    "trade_context_lookup": ("context", "atr", "macro", "event", "near macro", "session"),
}

PRIORITY = [
    "backtest_live_comparison",
    "risk_drift",
    "execution_quality",
    "regime_analysis",
    "performance_summary",
    "edge_decay",
    "trade_lookup",
    "journal_lookup",
    "trade_context_lookup",
]


def classify_intent(message: str) -> IntentClassification:
    normalized = message.lower().strip()
    matches: dict[str, list[str]] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        found = [keyword for keyword in keywords if keyword in normalized]
        if found:
            matches[intent] = found
    if not matches:
        return IntentClassification("unknown", [], 0.0, "no keyword matches")
    ranked = sorted(matches, key=lambda key: (-len(matches[key]), PRIORITY.index(key)))
    primary = ranked[0]
    confidence = min(1.0, 0.5 + (0.1 * len(matches[primary])))
    return IntentClassification(primary, ranked[1:], confidence, f"matched keywords -> {matches}")
