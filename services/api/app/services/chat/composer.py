from __future__ import annotations

from app.services.chat.safety import sanitize_answer

SUPPORTED = (
    "performance summary, regime sensitivity, slippage/execution, risk drift, "
    "edge decay, backtest-vs-live comparison, trades, journals, and trade context"
)

ANALYTICS_INTENTS = {
    "performance_summary",
    "regime_analysis",
    "execution_quality",
    "risk_drift",
    "edge_decay",
    "backtest_live_comparison",
}


def _sample_details(
    intent: str,
    analytics: dict,
    trades: list[dict],
    journal_entries: list[dict],
    trade_context: list[dict],
) -> tuple[int, str]:
    if intent == "journal_lookup":
        return len(journal_entries), "journal entries"
    if intent == "trade_context_lookup":
        return len(trade_context), "trade context records"
    if intent == "trade_lookup":
        return len(trades), "trades"
    if intent in ANALYTICS_INTENTS:
        size = analytics.get("sample_size") or analytics.get("total_trades") or len(trades)
        return int(size), "trades"
    return 0, "records"


def compose_answer(intent: str, analytics: dict, trades: list[dict], journal_entries: list[dict], trade_context: list[dict]) -> str:
    if intent == "unknown":
        return f"I can help analyze {SUPPORTED}. Try asking: 'Which volatility regime hurt me most?'"

    sample_size, evidence_label = _sample_details(intent, analytics, trades, journal_entries, trade_context)
    if sample_size < 5:
        return sanitize_answer(
            "I do not have enough matching "
            f"{evidence_label} to make a reliable comparison. "
            f"I found only {sample_size} matching {evidence_label} for this filter, "
            "so the result may not be statistically meaningful."
        )

    base = (
        f"Based on {sample_size} matching {evidence_label}, your historical data suggests "
        f"the matching sample shows {intent.replace('_', ' ')} patterns."
    )
    if trades:
        base += f" Evidence includes {len(trades)} trade records."
    if journal_entries:
        base += f" I also found {len(journal_entries)} journal entries."
    if trade_context:
        base += f" Trade context records matched: {len(trade_context)}."
    base += " This pattern was associated with historical outcomes; consider reviewing related setups and risk controls."
    return sanitize_answer(base)
