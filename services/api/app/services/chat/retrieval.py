from __future__ import annotations

from decimal import Decimal

from sqlalchemy import nullslast, or_, select

from app.models import JournalEntry, Trade, TradeContext
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def _to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _trade_to_dict(trade: Trade) -> dict:
    return {
        "trade_id": trade.id,
        "symbol": trade.symbol,
        "side": trade.side,
        "entry_time": trade.entry_time,
        "exit_time": trade.exit_time,
        "source_type": trade.source_type,
        "pnl": _to_float(trade.pnl),
        "r_multiple": _to_float(trade.r_multiple),
        "session_label": trade.session_label,
    }


def get_recent_trades(db, user_id, filters: AnalyticsFilters, limit: int = 10) -> list[dict]:
    stmt = apply_trade_filters(select(Trade), filters).order_by(Trade.entry_time.desc()).limit(limit)
    return [_trade_to_dict(trade) for trade in db.scalars(stmt).all()]


def get_worst_trades(db, user_id, filters: AnalyticsFilters, limit: int = 10) -> list[dict]:
    stmt = apply_trade_filters(select(Trade), filters).order_by(Trade.r_multiple.asc(), Trade.pnl.asc()).limit(limit)
    return [_trade_to_dict(trade) for trade in db.scalars(stmt).all()]


def get_best_trades(db, user_id, filters: AnalyticsFilters, limit: int = 10) -> list[dict]:
    stmt = (
        apply_trade_filters(select(Trade), filters)
        .where(or_(Trade.r_multiple.is_not(None), Trade.pnl.is_not(None)))
        .order_by(
            nullslast(Trade.r_multiple.desc()),
            nullslast(Trade.pnl.desc()),
            Trade.entry_time.desc(),
        )
        .limit(limit)
    )
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
        stmt = stmt.where(or_(JournalEntry.text.ilike(like), JournalEntry.title.ilike(like)))
    stmt = stmt.order_by(JournalEntry.entry_time.desc()).limit(limit)

    entries = db.scalars(stmt).all()
    return [
        {
            "journal_entry_id": entry.id,
            "trade_id": entry.trade_id,
            "entry_time": entry.entry_time,
            "title": entry.title,
            "text_excerpt": entry.text[:160],
        }
        for entry in entries
    ]


def get_trade_context_records(db, user_id, filters: AnalyticsFilters, limit: int = 10) -> list[dict]:
    stmt = apply_trade_filters(select(Trade), filters).limit(limit)
    trades = db.scalars(stmt).all()

    out: list[dict] = []
    for trade in trades:
        context: TradeContext | None = trade.trade_context
        if context is None:
            continue
        out.append(
            {
                "trade_id": trade.id,
                "trend_regime": context.trend_regime,
                "volatility_regime": context.volatility_regime,
                "macro_event_nearby": context.macro_event_nearby,
                "macro_event_name": context.macro_event_name,
                "minutes_to_event": context.minutes_to_event,
            }
        )
    return out
