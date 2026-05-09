from __future__ import annotations

from app.schemas.chat import ChatFilters, ChatResponse
from app.services.analytics import (
    AnalyticsFilters,
    compare_backtest_live,
    get_edge_decay,
    get_execution_quality,
    get_performance_summary,
    get_regime_sensitivity,
    get_risk_drift,
)
from app.services.chat.classifier import classify_intent
from app.services.chat.composer import compose_answer
from app.services.chat.retrieval import (
    get_best_trades,
    get_journal_entries,
    get_recent_trades,
    get_trade_context_records,
    get_worst_trades,
)
from app.services.chat.safety import is_direct_advice_request, safe_advice_refusal


def _analytics_filters(user_id, filters: ChatFilters) -> AnalyticsFilters:
    return AnalyticsFilters(user_id=user_id, strategy_id=filters.strategy_id, source_type=filters.source_type, symbol=filters.symbol, instrument=filters.instrument, start_date=filters.start_date, end_date=filters.end_date)


def handle_chat_message(db, user_id, message: str, filters: ChatFilters) -> ChatResponse:
    if is_direct_advice_request(message):
        return ChatResponse(intent="unknown", secondary_intents=[], answer=safe_advice_refusal(), evidence={"analytics": {}, "trades": [], "journal_entries": [], "trade_context": []}, filters=filters, warnings=["direct_trading_advice_refused"], suggested_questions=["How has my risk drift changed in the last 30 trades?"])

    classification = classify_intent(message)
    af = _analytics_filters(user_id, filters)
    analytics: dict = {}
    trades: list[dict] = []
    journal_entries: list[dict] = []
    trade_context: list[dict] = []
    text = message.lower()

    if classification.primary_intent == "performance_summary":
        analytics = get_performance_summary(db, af)
        trades = get_worst_trades(db, user_id, af, filters.limit) if any(k in text for k in ("loss", "underperform", "bad", "drawdown")) else get_recent_trades(db, user_id, af, filters.limit)
    elif classification.primary_intent == "regime_analysis":
        group_by = "volatility_regime"
        if any(k in text for k in ("trend", "ranging")): group_by = "trend_regime"
        elif any(k in text for k in ("session", "time", "open", "close")): group_by = "session_label"
        elif any(k in text for k in ("news", "macro", "cpi", "fomc", "event")): group_by = "macro_event_nearby"
        analytics = get_regime_sensitivity(db, af, group_by)
    elif classification.primary_intent == "execution_quality":
        group_by = "session_label"
        if any(k in text for k in ("order", "fill")): group_by = "order_type"
        elif any(k in text for k in ("instrument", "symbol")): group_by = "symbol"
        elif "volatility" in text: group_by = "volatility_regime"
        analytics = get_execution_quality(db, af, group_by)
    elif classification.primary_intent == "risk_drift": analytics = get_risk_drift(db, af)
    elif classification.primary_intent == "edge_decay": analytics = get_edge_decay(db, af)
    elif classification.primary_intent == "backtest_live_comparison": analytics = compare_backtest_live(db, af)
    elif classification.primary_intent == "trade_lookup":
        trades = get_worst_trades(db, user_id, af, filters.limit) if "worst" in text or "losing" in text else get_best_trades(db, user_id, af, filters.limit) if "best" in text or "winning" in text else get_recent_trades(db, user_id, af, filters.limit)
    elif classification.primary_intent == "journal_lookup":
        journal_entries = get_journal_entries(db, user_id, af, query=message, limit=filters.limit)
    elif classification.primary_intent == "trade_context_lookup":
        trade_context = get_trade_context_records(db, user_id, af, filters.limit)

    answer = compose_answer(classification.primary_intent, analytics, trades, journal_entries, trade_context)
    return ChatResponse(intent=classification.primary_intent, secondary_intents=classification.secondary_intents, answer=answer, evidence={"analytics": analytics, "trades": trades, "journal_entries": journal_entries, "trade_context": trade_context}, filters=filters, warnings=[], suggested_questions=["Which volatility regime hurt me most?", "Is live performance drifting from backtest?"])
