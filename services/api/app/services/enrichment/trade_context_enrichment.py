from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade, TradeContext

logger = logging.getLogger(__name__)
TREND_SLOPE_THRESHOLD = Decimal("0.0001")


class MarketDataProvider(Protocol):
    def get_snapshot(self, symbol: str, timestamp: datetime) -> dict[str, Any] | None: ...
    def get_atr_percentile(self, symbol: str, timestamp: datetime) -> Decimal | float | None: ...
    def get_realized_vol_percentile(self, symbol: str, timestamp: datetime) -> Decimal | float | None: ...
    def get_trend_inputs(self, symbol: str, timestamp: datetime) -> dict[str, Decimal | float] | None: ...


class EventProvider(Protocol):
    def get_nearest_event(self, timestamp: datetime, symbol: str | None = None) -> dict[str, Any] | None: ...


@dataclass
class BatchEnrichmentSummary:
    processed: int = 0
    enriched: int = 0
    skipped: int = 0
    errors: int = 0


def _to_decimal(value: Decimal | float | int | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _compute_session_label(entry_time: datetime) -> str:
    hour = entry_time.astimezone(timezone.utc).hour
    if 0 <= hour <= 6:
        return "asia"
    if 7 <= hour <= 12:
        return "london"
    if 13 <= hour <= 15:
        return "ny_open"
    if 16 <= hour <= 19:
        return "ny_mid"
    if 20 <= hour <= 21:
        return "ny_close"
    return "after_hours"


def _volatility_regime(atr_percentile: Decimal | None) -> str | None:
    if atr_percentile is None:
        return None
    if atr_percentile <= Decimal("33"):
        return "low"
    if atr_percentile <= Decimal("66"):
        return "medium"
    return "high"


def _trend_regime(trend_inputs: dict[str, Decimal | float] | None, realized_vol_percentile: Decimal | None) -> str | None:
    if trend_inputs is None:
        return None
    close = _to_decimal(trend_inputs.get("close"))
    ma_50 = _to_decimal(trend_inputs.get("ma_50"))
    ma_50_slope = _to_decimal(trend_inputs.get("ma_50_slope"))
    if close is None or ma_50 is None or ma_50_slope is None:
        return None
    if close > ma_50 and ma_50_slope > TREND_SLOPE_THRESHOLD:
        return "trending_up"
    if close < ma_50 and ma_50_slope < -TREND_SLOPE_THRESHOLD:
        return "trending_down"
    if realized_vol_percentile is not None and realized_vol_percentile > Decimal("80"):
        return "volatile"
    return "ranging"


def enrich_trade_context(db: Session, trade_id: UUID, market_data_provider: MarketDataProvider | None = None, event_provider: EventProvider | None = None) -> TradeContext:
    trade = db.scalar(select(Trade).where(Trade.id == trade_id))
    if trade is None:
        raise ValueError("trade_not_found")

    entry_time = trade.entry_time
    context_payload: dict[str, Any] = {}
    session_label = trade.session_label or _compute_session_label(entry_time)
    context_payload["session_source"] = "trade" if trade.session_label else "computed"
    context_payload["session_label"] = session_label
    context_payload["holding_minutes"] = int((trade.exit_time - trade.entry_time).total_seconds() // 60) if trade.exit_time else None

    atr_percentile = realized_vol_percentile = vix_level = volume_percentile = None
    spread_at_entry = spread_at_exit = liquidity_score = None
    trend_inputs = None
    if market_data_provider is not None:
        atr_percentile = _to_decimal(market_data_provider.get_atr_percentile(trade.symbol, entry_time))
        realized_vol_percentile = _to_decimal(market_data_provider.get_realized_vol_percentile(trade.symbol, entry_time))
        trend_inputs = market_data_provider.get_trend_inputs(trade.symbol, entry_time)
        snapshot = market_data_provider.get_snapshot(trade.symbol, entry_time) or {}
        vix_level = _to_decimal(snapshot.get("vix_level"))
        volume_percentile = _to_decimal(snapshot.get("volume_percentile"))
        spread_at_entry = _to_decimal(snapshot.get("spread_at_entry"))
        spread_at_exit = _to_decimal(snapshot.get("spread_at_exit"))
        liquidity_score = _to_decimal(snapshot.get("liquidity_score"))
        context_payload["atr_source"] = "market_data_provider"
    else:
        logger.info("market_data_provider_missing", extra={"trade_id": str(trade_id), "symbol": trade.symbol})

    macro_event_nearby = macro_event_name = minutes_to_event = None
    if event_provider is not None:
        nearest = event_provider.get_nearest_event(entry_time, symbol=trade.symbol)
        if nearest is not None:
            event_time: datetime = nearest["timestamp"]
            minutes_to_event = int(abs((event_time - entry_time).total_seconds()) // 60)
            macro_event_nearby = minutes_to_event <= 120
            macro_event_name = nearest.get("name")
    else:
        logger.info("event_provider_missing", extra={"trade_id": str(trade_id), "symbol": trade.symbol})

    context_payload["trend_inputs"] = trend_inputs
    volatility_regime = _volatility_regime(atr_percentile)
    trend_regime = _trend_regime(trend_inputs, realized_vol_percentile)

    context = db.scalar(select(TradeContext).where(TradeContext.trade_id == trade_id))
    if context is None:
        context = TradeContext(trade_id=trade_id)
        db.add(context)

    context.atr_percentile = atr_percentile
    context.realized_vol_percentile = realized_vol_percentile
    context.vix_level = vix_level
    context.volume_percentile = volume_percentile
    context.trend_regime = trend_regime
    context.volatility_regime = volatility_regime
    context.macro_event_nearby = macro_event_nearby
    context.macro_event_name = macro_event_name
    context.minutes_to_event = minutes_to_event
    context.spread_at_entry = spread_at_entry
    context.spread_at_exit = spread_at_exit
    context.liquidity_score = liquidity_score
    context.context_payload = context_payload
    db.flush()
    logger.info("trade_enriched", extra={"trade_id": str(trade_id), "symbol": trade.symbol, "result": "enriched"})
    return context


def batch_enrich_trade_context(db: Session, strategy_id: UUID | None = None, source_type: str | None = None, symbol: str | None = None, start_date: datetime | None = None, end_date: datetime | None = None, limit: int | None = None, skip_existing: bool = False, market_data_provider: MarketDataProvider | None = None, event_provider: EventProvider | None = None) -> BatchEnrichmentSummary:
    summary = BatchEnrichmentSummary()
    stmt = select(Trade)
    if strategy_id is not None:
        stmt = stmt.where(Trade.strategy_id == strategy_id)
    if source_type is not None:
        stmt = stmt.where(Trade.source_type == source_type)
    if symbol is not None:
        stmt = stmt.where(Trade.symbol == symbol)
    if start_date is not None:
        stmt = stmt.where(Trade.entry_time >= start_date)
    if end_date is not None:
        stmt = stmt.where(Trade.entry_time <= end_date)
    if limit is not None:
        stmt = stmt.limit(limit)

    for trade in db.scalars(stmt).all():
        summary.processed += 1
        try:
            if skip_existing and db.scalar(select(TradeContext).where(TradeContext.trade_id == trade.id)) is not None:
                summary.skipped += 1
                continue
            enrich_trade_context(db, trade.id, market_data_provider=market_data_provider, event_provider=event_provider)
            summary.enriched += 1
        except Exception:
            summary.errors += 1
            logger.exception("trade_enrichment_failed", extra={"trade_id": str(trade.id), "symbol": trade.symbol})
    db.commit()
    return summary
