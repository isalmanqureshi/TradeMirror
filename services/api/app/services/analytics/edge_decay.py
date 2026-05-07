from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def get_edge_decay(db: Session, filters: AnalyticsFilters, window_size: int = 20) -> dict:
    stmt = apply_trade_filters(select(Trade).order_by(Trade.entry_time), filters)
    trades = [trade for trade in db.scalars(stmt).all() if trade.r_multiple is not None]

    if len(trades) < window_size:
        return {
            "filters": filters.__dict__,
            "window_size": window_size,
            "sample_size": len(trades),
            "points": [],
            "message": "Insufficient trades for requested window size",
        }

    points: list[dict] = []
    for idx in range(window_size - 1, len(trades)):
        window = trades[idx - window_size + 1 : idx + 1]
        r_values = [float(trade.r_multiple) for trade in window]
        wins = [value for value in r_values if value > 0]
        losses = [value for value in r_values if value < 0]

        profit_factor = (sum(wins) / abs(sum(losses))) if losses else None

        points.append(
            {
                "entry_time": trades[idx].entry_time,
                "trade_id": str(trades[idx].id),
                "rolling_average_r": sum(r_values) / len(r_values),
                "rolling_win_rate": len(wins) / len(r_values),
                "rolling_profit_factor": profit_factor,
                "rolling_expectancy_r": sum(r_values) / len(r_values),
                "sample_size": window_size,
            }
        )

    return {
        "filters": filters.__dict__,
        "window_size": window_size,
        "sample_size": len(trades),
        "points": points,
        "message": None,
    }
