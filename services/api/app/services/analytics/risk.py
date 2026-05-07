from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def get_risk_drift(db: Session, filters: AnalyticsFilters) -> dict:
    trades = db.scalars(apply_trade_filters(select(Trade), filters)).all()

    risk_rows = [
        trade
        for trade in trades
        if trade.planned_risk is not None and trade.actual_risk is not None
    ]

    deltas = [float(trade.actual_risk - trade.planned_risk) for trade in risk_rows]
    delta_pct = [
        float((trade.actual_risk - trade.planned_risk) / trade.planned_risk)
        for trade in risk_rows
        if float(trade.planned_risk) != 0
    ]

    oversized = [
        trade
        for trade in risk_rows
        if float(trade.actual_risk) > float(trade.planned_risk) * 1.25
    ]

    return {
        "filters": filters.__dict__,
        "sample_size": len(trades),
        "risk_sample_size": len(risk_rows),
        "planned_risk_avg": (
            (sum(float(trade.planned_risk) for trade in risk_rows) / len(risk_rows))
            if risk_rows
            else None
        ),
        "actual_risk_avg": (
            (sum(float(trade.actual_risk) for trade in risk_rows) / len(risk_rows))
            if risk_rows
            else None
        ),
        "average_risk_delta": (sum(deltas) / len(deltas)) if deltas else None,
        "average_risk_delta_pct": (sum(delta_pct) / len(delta_pct)) if delta_pct else None,
        "max_actual_risk": max((float(trade.actual_risk) for trade in risk_rows), default=None),
        "oversized_trade_count": len(oversized),
        "oversized_trade_rate": (len(oversized) / len(risk_rows)) if risk_rows else None,
    }
