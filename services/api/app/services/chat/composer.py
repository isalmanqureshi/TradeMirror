from __future__ import annotations

from app.services.chat.safety import sanitize_answer

SUPPORTED = (
    "performance summary, regime sensitivity, slippage/execution, risk drift, "
    "edge decay, backtest-vs-live comparison, trades, journals, and trade context"
)


def _sum_group_sample_size(groups: list[dict]) -> int:
    return sum(int(group.get("sample_size", 0) or 0) for group in groups)


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

    if intent == "performance_summary":
        return int(analytics.get("sample_size") or len(trades)), "trades"
    if intent == "regime_analysis":
        groups = analytics.get("groups") or []
        return _sum_group_sample_size(groups) or len(trades), "trades"
    if intent == "execution_quality":
        groups = analytics.get("groups") or []
        if groups:
            return _sum_group_sample_size(groups), "trades"
        return int(analytics.get("sample_size") or len(trades)), "trades"
    if intent == "backtest_live_comparison":
        bt = int(analytics.get("backtest_sample_size") or 0)
        live = int(analytics.get("live_sample_size") or 0)
        total = bt + live
        return (total or len(trades)), "trades"
    if intent == "edge_decay":
        points = analytics.get("points") or []
        return int(analytics.get("sample_size") or len(points) or len(trades)), "trades"
    if intent == "risk_drift":
        risk_size = analytics.get("sample_size")
        if risk_size is None:
            risk_size = analytics.get("risk_sample_size") or analytics.get("planned_risk_sample_size") or analytics.get("actual_risk_sample_size")
        return int(risk_size or len(trades)), "trades"

    return len(trades), "trades"


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
