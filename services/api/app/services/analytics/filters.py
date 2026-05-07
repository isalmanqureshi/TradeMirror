from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select

from app.models import Trade


@dataclass(frozen=True)
class AnalyticsFilters:
    user_id: UUID
    strategy_id: UUID | None = None
    source_type: str | None = None
    symbol: str | None = None
    instrument: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


def apply_trade_filters(stmt: Select, filters: AnalyticsFilters) -> Select:
    stmt = stmt.where(Trade.user_id == filters.user_id)

    if filters.strategy_id is not None:
        stmt = stmt.where(Trade.strategy_id == filters.strategy_id)
    if filters.source_type is not None:
        stmt = stmt.where(Trade.source_type == filters.source_type)
    if filters.symbol is not None:
        stmt = stmt.where(Trade.symbol == filters.symbol)
    if filters.instrument is not None:
        stmt = stmt.where(Trade.instrument == filters.instrument)
    if filters.start_date is not None:
        stmt = stmt.where(Trade.entry_time >= filters.start_date)
    if filters.end_date is not None:
        stmt = stmt.where(Trade.entry_time <= filters.end_date)

    return stmt
