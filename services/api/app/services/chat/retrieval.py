from __future__ import annotations

from decimal import Decimal

from sqlalchemy import case, nullslast, or_, select

from app.models import JournalEntry, Trade, TradeContext
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def _to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _trade_to_dict(trade: Trade) -> dict:
    return {
        "trade_id": trade.id,
        "strategy_id": trade.strategy_id,
        "symbol": trade.symbol,
        "instrument": trade.instrument,
        "source_type": trade.source_type,
        "side": trade.side,
        "entry_time": trade.entry_time,
        "exit_time": trade.exit_time,
        "pnl": _to_float(trade.pnl),
        "r_multiple": _to_float(trade.r_multiple),
        "session_label": trade.session_label,
        "order_type": trade.order_type,
    }


def get_recent_trades(db, user_id, filters: AnalyticsFilters, limit: int = 10) -> list[dict]:
    stmt = apply_trade_filters(select(Trade), filters).order_by(Trade.entry_time.desc(), Trade.id.desc()).limit(limit)
    return [_trade_to_dict(trade) for trade in db.scalars(stmt).all()]


def get_worst_trades(db, user_id, filters: AnalyticsFilters, limit: int = 10) -> list[dict]:
    stmt = apply_trade_filters(select(Trade), filters).order_by(Trade.r_multiple.asc(), Trade.pnl.asc(), Trade.entry_time.desc(), Trade.id.desc()).limit(limit)
    return [_trade_to_dict(trade) for trade in db.scalars(stmt).all()]


def get_best_trades(db, user_id, filters: AnalyticsFilters, limit: int = 10) -> list[dict]:
    stmt = apply_trade_filters(select(Trade), filters).where(or_(Trade.r_multiple.is_not(None), Trade.pnl.is_not(None))).order_by(nullslast(Trade.r_multiple.desc()), nullslast(Trade.pnl.desc()), Trade.entry_time.desc(), Trade.id.desc()).limit(limit)
    return [_trade_to_dict(trade) for trade in db.scalars(stmt).all()]


def get_journal_entries(db, user_id, filters: AnalyticsFilters, query: str | None = None, limit: int = 10) -> list[dict]:
    stmt = select(JournalEntry).where(JournalEntry.user_id == user_id)
    if filters.strategy_id is not None:
        stmt = stmt.where(JournalEntry.strategy_id == filters.strategy_id)
    if filters.start_date is not None:
        stmt = stmt.where(JournalEntry.entry_time >= filters.start_date)
    if filters.end_date is not None:
        stmt = stmt.where(JournalEntry.entry_time <= filters.end_date)
    if query:
        like = f"%{query.lower()}%"
        relevance = case((JournalEntry.title.ilike(like), 2), (JournalEntry.text.ilike(like), 1), else_=0)
        stmt = stmt.where(or_(JournalEntry.text.ilike(like), JournalEntry.title.ilike(like))).order_by(relevance.desc(), JournalEntry.entry_time.desc(), JournalEntry.created_at.desc())
    else:
        stmt = stmt.order_by(JournalEntry.entry_time.desc(), JournalEntry.created_at.desc())
    entries = db.scalars(stmt.limit(limit)).all()
    return [{"journal_entry_id": e.id, "trade_id": e.trade_id, "strategy_id": e.strategy_id, "entry_time": e.entry_time, "title": e.title, "text_excerpt": (e.text or "")[:240], "emotion_tags": e.emotion_tags or [], "mistake_tags": e.mistake_tags or []} for e in entries]


def get_trade_context_records(db, user_id, filters: AnalyticsFilters, limit: int = 10) -> list[dict]:
    has_context = case(((TradeContext.trend_regime.is_not(None), 1),), else_=0) + case(((TradeContext.volatility_regime.is_not(None), 1),), else_=0) + case(((TradeContext.atr_percentile.is_not(None), 1),), else_=0)
    stmt = apply_trade_filters(select(Trade, TradeContext).join(TradeContext, TradeContext.trade_id == Trade.id), filters).order_by(has_context.desc(), Trade.entry_time.desc(), Trade.id.desc()).limit(limit)
    rows = db.execute(stmt).all()
    return [{"trade_id": t.id, "symbol": t.symbol, "entry_time": t.entry_time, "trend_regime": c.trend_regime, "volatility_regime": c.volatility_regime, "atr_percentile": _to_float(c.atr_percentile), "realized_vol_percentile": _to_float(c.realized_vol_percentile), "macro_event_nearby": c.macro_event_nearby, "macro_event_name": c.macro_event_name, "minutes_to_event": c.minutes_to_event} for t, c in rows]
