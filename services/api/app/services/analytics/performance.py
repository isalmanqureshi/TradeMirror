from __future__ import annotations

from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def _profit_factor(values: list[float]) -> float | None:
    wins = sum(value for value in values if value > 0)
    losses = abs(sum(value for value in values if value < 0))
    if losses == 0:
        return None
    return wins / losses


def get_performance_summary(db: Session, filters: AnalyticsFilters) -> dict:
    stmt = apply_trade_filters(select(Trade), filters)
    trades = db.scalars(stmt).all()

    pnl_values = [float(trade.pnl) for trade in trades if trade.pnl is not None]
    r_values = [float(trade.r_multiple) for trade in trades if trade.r_multiple is not None]

    outcome_values = r_values if r_values else pnl_values
    wins = [value for value in outcome_values if value > 0]
    losses = [value for value in outcome_values if value < 0]

    cumulative_r = 0.0
    peak_r = 0.0
    max_drawdown_r = 0.0
    for value in r_values:
        cumulative_r += value
        peak_r = max(peak_r, cumulative_r)
        max_drawdown_r = max(max_drawdown_r, peak_r - cumulative_r)

    total_fees = sum(float(trade.fees) for trade in trades if trade.fees is not None)
    net_pnl = sum(pnl_values) if pnl_values else None

    positive_r = [value for value in r_values if value > 0]
    negative_r = [value for value in r_values if value < 0]

    return {
        "filters": filters.__dict__,
        "sample_size": len(trades),
        "net_pnl": net_pnl,
        "total_fees": total_fees if trades else None,
        "gross_pnl": (net_pnl + total_fees) if net_pnl is not None else None,
        "win_rate": (len(wins) / len(outcome_values)) if outcome_values else None,
        "loss_rate": (len(losses) / len(outcome_values)) if outcome_values else None,
        "average_r": (sum(r_values) / len(r_values)) if r_values else None,
        "median_r": median(r_values) if r_values else None,
        "expectancy_r": (sum(r_values) / len(r_values)) if r_values else None,
        "average_win_r": (sum(positive_r) / len(positive_r)) if positive_r else None,
        "average_loss_r": (sum(negative_r) / len(negative_r)) if negative_r else None,
        "profit_factor": _profit_factor(r_values if r_values else pnl_values),
        "largest_win_r": max(r_values) if r_values else None,
        "largest_loss_r": min(r_values) if r_values else None,
        "max_drawdown_r": max_drawdown_r if r_values else None,
    }
