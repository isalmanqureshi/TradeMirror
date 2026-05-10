from __future__ import annotations

from app.services.chat.safety import sanitize_answer

SUPPORTED_CAPABILITIES = (
    "imported trade data, journal entries, enriched trade context, and analytics summaries"
)

INTENT_SUGGESTIONS: dict[str, list[str]] = {
    "performance_summary": [
        "Which trades contributed most to the drawdown?",
        "Which volatility regime hurt performance most?",
        "How does live performance compare with the backtest?",
    ],
    "regime_analysis": [
        "Which regime has the best average R?",
        "How many trades were taken in high volatility?",
        "Which session performs best during high volatility?",
    ],
    "execution_quality": [
        "Which session has the worst slippage?",
        "Do market orders have higher slippage than limit orders?",
        "Which symbol has the highest execution cost?",
    ],
    "risk_drift": [
        "How often did actual risk exceed planned risk?",
        "Which trades were oversized?",
        "Is risk drift getting worse over time?",
    ],
    "edge_decay": [
        "When did rolling expectancy turn negative?",
        "Which recent trades caused the edge decay?",
        "Compare the latest 20 trades with the previous 20.",
    ],
    "backtest_live_comparison": [
        "Is live average R lower than backtest average R?",
        "Which live trades differ most from backtest assumptions?",
        "Is win rate or average loss driving the drift?",
    ],
    "trade_lookup": [
        "Show my worst 10 trades.",
        "Show trades from high volatility periods.",
        "Show recent losing trades with journal notes.",
    ],
    "journal_lookup": [
        "Which mistakes appear most often?",
        "Show notes tagged with FOMO or revenge trading.",
        "Which journal entries are linked to large losses?",
    ],
    "trade_context_lookup": [
        "Show trades near macro events.",
        "Which trades happened in high ATR conditions?",
        "Which sessions have the most enriched context?",
    ],
    "unknown": [
        "How did my strategy perform?",
        "Which session has the worst slippage?",
        "Is live performance drifting from the backtest?",
    ],
}


def safe_float(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def format_number(value: object, decimals: int = 2) -> str:
    number = safe_float(value)
    if number is None:
        return "not available"
    return f"{number:.{decimals}f}"


def format_percent(value: object) -> str:
    number = safe_float(value)
    if number is None:
        return "not available"
    return f"{number * 100:.0f}%"


def format_r(value: object) -> str:
    number = safe_float(value)
    if number is None:
        return "not available"
    return f"{number:.2f}R"


def format_money(value: object, with_currency: bool = False) -> str:
    amount = format_number(value)
    return f"${amount}" if with_currency and amount != "not available" else amount


def _sample_size(intent: str, analytics: dict, trades: list[dict], journal_entries: list[dict], trade_context: list[dict]) -> int:
    if intent == "journal_lookup":
        return len(journal_entries)
    if intent == "trade_context_lookup":
        return len(trade_context)
    if intent == "trade_lookup":
        return len(trades)
    if intent == "backtest_live_comparison":
        return int(analytics.get("backtest_sample_size") or 0) + int(analytics.get("live_sample_size") or 0)
    if intent in {"regime_analysis", "execution_quality"}:
        groups = analytics.get("groups") or []
        return sum(int(group.get("sample_size") or 0) for group in groups)
    return int(analytics.get("sample_size") or len(trades))


def build_warnings(intent: str, analytics: dict, journal_entries: list[dict], trade_context: list[dict], sample_size: int) -> list[str]:
    warnings: list[str] = []
    if sample_size < 10 and intent != "unknown":
        warnings.append("Sample size is small, so treat this as directional rather than statistically reliable.")
    if intent == "backtest_live_comparison":
        if min(int(analytics.get("backtest_sample_size") or 0), int(analytics.get("live_sample_size") or 0)) < 10:
            warnings.append("Backtest/live comparison is limited because one side has fewer than the recommended minimum trades.")
    if intent == "journal_lookup" and not journal_entries:
        warnings.append("No matching journal entries were found. The answer is based only on structured trade data.")
    if intent in {"regime_analysis", "trade_context_lookup"} and trade_context:
        populated = sum(1 for row in trade_context if row.get("trend_regime") or row.get("volatility_regime") or row.get("atr_percentile") is not None)
        if populated < max(1, len(trade_context) // 2):
            warnings.append("Some trades are missing enriched market context, so regime-level conclusions may be incomplete.")
    if intent == "unknown":
        warnings.append("I can analyze imported trade data, journal entries, enriched context, and analytics summaries.")
    return warnings


def compose_answer(intent: str, analytics: dict, trades: list[dict], journal_entries: list[dict], trade_context: list[dict], warnings: list[str] | None = None) -> str:
    warnings = warnings or []
    next_question = INTENT_SUGGESTIONS.get(intent, INTENT_SUGGESTIONS["unknown"])[0]

    if intent == "unknown":
        answer = (
            f"I can help with {SUPPORTED_CAPABILITIES}. "
            f"Try asking about performance, execution quality, risk drift, journal patterns, or market-context behavior. "
            f"You may want to ask: {next_question}"
        )
        return sanitize_answer(answer)

    sample_size = _sample_size(intent, analytics, trades, journal_entries, trade_context)
    caveat = warnings[0] if warnings else None

    if intent in {"performance_summary", "regime_analysis", "execution_quality", "risk_drift", "edge_decay", "backtest_live_comparison"}:
        win_rate = format_percent(analytics.get("win_rate"))
        avg_r = format_r(analytics.get("average_r"))
        pnl = format_money(analytics.get("net_pnl"))
        evidence_summary = f"Evidence includes {len(trades)} trades, {len(journal_entries)} journal entries, and {len(trade_context)} context records."
        answer = (
            f"Based on {sample_size} matching trades, this {intent.replace('_', ' ')} view shows win rate {win_rate}, average R {avg_r}, and net PnL {pnl}. "
            f"{evidence_summary} "
            f"You may want to ask: {next_question}"
        )
    elif intent == "trade_lookup":
        answer = (
            f"I found {len(trades)} matching trades after applying your filters. "
            f"Top evidence includes symbols like {', '.join(sorted({t.get('symbol') for t in trades if t.get('symbol')})) or 'not available'}. "
            f"You may want to ask: {next_question}"
        )
    elif intent == "journal_lookup":
        answer = (
            f"I found {len(journal_entries)} matching journal entries and summarized the most relevant notes. "
            f"Filters were applied to your current strategy/date constraints. "
            f"You may want to ask: {next_question}"
        )
    else:
        answer = (
            f"I found {len(trade_context)} matching context records with recent trade-context evidence. "
            f"You may want to ask: {next_question}"
        )

    if caveat:
        answer = f"{answer} Caveat: {caveat}"
    return sanitize_answer(answer)
