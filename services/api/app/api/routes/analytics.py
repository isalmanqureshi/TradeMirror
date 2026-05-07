from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics import (
    AnalyticsFilters,
    compare_backtest_live,
    get_edge_decay,
    get_execution_quality,
    get_performance_summary,
    get_regime_sensitivity,
    get_risk_drift,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _filters(
    user_id: UUID,
    strategy_id: UUID | None,
    source_type: str | None,
    symbol: str | None,
    instrument: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
) -> AnalyticsFilters:
    return AnalyticsFilters(
        user_id=user_id,
        strategy_id=strategy_id,
        source_type=source_type,
        symbol=symbol,
        instrument=instrument,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/summary")
def summary(
    user_id: UUID,
    strategy_id: UUID | None = None,
    source_type: str | None = None,
    symbol: str | None = None,
    instrument: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict:
    return get_performance_summary(
        db,
        _filters(user_id, strategy_id, source_type, symbol, instrument, start_date, end_date),
    )


@router.get("/regime-sensitivity")
def regime_sensitivity(
    user_id: UUID,
    group_by: str = Query(default="volatility_regime"),
    strategy_id: UUID | None = None,
    source_type: str | None = None,
    symbol: str | None = None,
    instrument: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict:
    return get_regime_sensitivity(
        db,
        _filters(user_id, strategy_id, source_type, symbol, instrument, start_date, end_date),
        group_by,
    )


@router.get("/execution-quality")
def execution_quality(
    user_id: UUID,
    group_by: str = Query(default="session_label"),
    strategy_id: UUID | None = None,
    source_type: str | None = None,
    symbol: str | None = None,
    instrument: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict:
    return get_execution_quality(
        db,
        _filters(user_id, strategy_id, source_type, symbol, instrument, start_date, end_date),
        group_by,
    )


@router.get("/risk-drift")
def risk_drift(
    user_id: UUID,
    strategy_id: UUID | None = None,
    source_type: str | None = None,
    symbol: str | None = None,
    instrument: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict:
    return get_risk_drift(
        db,
        _filters(user_id, strategy_id, source_type, symbol, instrument, start_date, end_date),
    )


@router.get("/edge-decay")
def edge_decay(
    user_id: UUID,
    window_size: int = Query(default=20, ge=2),
    strategy_id: UUID | None = None,
    source_type: str | None = None,
    symbol: str | None = None,
    instrument: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict:
    return get_edge_decay(
        db,
        _filters(user_id, strategy_id, source_type, symbol, instrument, start_date, end_date),
        window_size,
    )


@router.get("/backtest-live-comparison")
def backtest_live(
    user_id: UUID,
    strategy_id: UUID | None = None,
    symbol: str | None = None,
    instrument: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict:
    return compare_backtest_live(
        db,
        _filters(user_id, strategy_id, None, symbol, instrument, start_date, end_date),
    )
