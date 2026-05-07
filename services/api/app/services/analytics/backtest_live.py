from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def compare_backtest_live(db: Session, filters: AnalyticsFilters) -> dict:
    trades = [
        trade
        for trade in db.scalars(apply_trade_filters(select(Trade), filters)).all()
        if trade.r_multiple is not None
    ]

    backtest_r = [float(trade.r_multiple) for trade in trades if trade.source_type == "backtest"]
    live_r = [float(trade.r_multiple) for trade in trades if trade.source_type == "live"]

    if len(backtest_r) < 5 or len(live_r) < 5:
        return {
            "filters": filters.__dict__,
            "status": "insufficient_data",
            "backtest_sample_size": len(backtest_r),
            "live_sample_size": len(live_r),
            "ks_test": None,
            "message": "Insufficient sample sizes: require backtest>=5 and live>=5",
        }

    backtest_average_r = sum(backtest_r) / len(backtest_r)
    live_average_r = sum(live_r) / len(live_r)
    backtest_win_rate = len([value for value in backtest_r if value > 0]) / len(backtest_r)
    live_win_rate = len([value for value in live_r if value > 0]) / len(live_r)

    return {
        "filters": filters.__dict__,
        "status": "ok",
        "backtest_sample_size": len(backtest_r),
        "live_sample_size": len(live_r),
        "backtest_average_r": backtest_average_r,
        "live_average_r": live_average_r,
        "backtest_win_rate": backtest_win_rate,
        "live_win_rate": live_win_rate,
        "expectancy_delta": live_average_r - backtest_average_r,
        "average_r_delta": live_average_r - backtest_average_r,
        "win_rate_delta": live_win_rate - backtest_win_rate,
        "ks_test": None,
        "message": "Statistical test not available in this phase",
    }
