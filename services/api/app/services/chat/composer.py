from __future__ import annotations

from app.services.chat.safety import sanitize_answer


SUPPORTED = "performance summary, regime sensitivity, slippage/execution, risk drift, edge decay, backtest-vs-live comparison, trades, journals, and trade context"


def compose_answer(intent: str, analytics: dict, trades: list[dict], journal_entries: list[dict], trade_context: list[dict]) -> str:
    if intent == "unknown":
        return f"I can help analyze {SUPPORTED}. Try asking: 'Which volatility regime hurt me most?'"

    sample_size = analytics.get("sample_size") or analytics.get("total_trades") or len(trades)
    if sample_size < 5:
        return sanitize_answer(
            f"I do not have enough matching trades to make a reliable comparison. I found only {sample_size} matching trades for this filter, so the result may not be statistically meaningful."
        )

    base = f"Based on {sample_size} matching trades, your historical data suggests the matching sample shows {intent.replace('_', ' ')} patterns."
    if trades:
        base += f" Evidence includes {len(trades)} trade records."
    if journal_entries:
        base += f" I also found {len(journal_entries)} journal entries."
    if trade_context:
        base += f" Trade context records matched: {len(trade_context)}."
    base += " This pattern was associated with historical outcomes; consider reviewing related setups and risk controls."
    return sanitize_answer(base)
