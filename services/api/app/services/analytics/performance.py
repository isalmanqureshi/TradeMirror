from __future__ import annotations

from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def _profit_factor(values: list[float]) -> float | None:
    wins = sum(v for v in values if v > 0)
    losses = abs(sum(v for v in values if v < 0))
    if losses == 0:
        return None
    return wins / losses


def get_performance_summary(db: Session, filters: AnalyticsFilters) -> dict:
    stmt = apply_trade_filters(select(Trade), filters)
    trades = db.scalars(stmt).all()
    pnl_values = [float(t.pnl) for t in trades if t.pnl is not None]
    r_values = [float(t.r_multiple) for t in trades if t.r_multiple is not None]
    outcome_values = r_values if r_values else pnl_values
    wins = [v for v in outcome_values if v > 0]
    losses = [v for v in outcome_values if v < 0]

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in r_values:
        cumulative += r
        peak = max(peak, cumulative)
        max_dd = max(max_dd, peak - cumulative)

    total_fees = sum(float(t.fees) for t in trades if t.fees is not None)
    net_pnl = sum(pnl_values) if pnl_values else None

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
        "average_win_r": (sum(v for v in r_values if v > 0) / len([v for v in r_values if v > 0])) if any(v > 0 for v in r_values) else None,
        "average_loss_r": (sum(v for v in r_values if v < 0) / len([v for v in r_values if v < 0])) if any(v < 0 for v in r_values) else None,
        "profit_factor": _profit_factor(r_values if r_values else pnl_values),
        "largest_win_r": max(r_values) if r_values else None,
        "largest_loss_r": min(r_values) if r_values else None,
        "max_drawdown_r": max_dd if r_values else None,
    }
