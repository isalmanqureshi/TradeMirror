from __future__ import annotations

from collections import defaultdict
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters

CONTEXT_FIELDS = {"trend_regime", "volatility_regime", "macro_event_nearby"}


def get_regime_sensitivity(db: Session, filters: AnalyticsFilters, group_by: str) -> dict:
    stmt = apply_trade_filters(select(Trade), filters)
    trades = db.scalars(stmt).all()

    grouped: dict[str, list[Trade]] = defaultdict(list)
    for trade in trades:
        if group_by in CONTEXT_FIELDS:
            key = getattr(trade.trade_context, group_by, None)
        else:
            key = getattr(trade, group_by, None)
        grouped[str(key).lower() if key is not None else "unknown"].append(trade)

    groups: list[dict] = []
    for key, items in grouped.items():
        r_values = [float(item.r_multiple) for item in items if item.r_multiple is not None]
        pnl_values = [float(item.pnl) for item in items if item.pnl is not None]
        outcomes = r_values if r_values else pnl_values

        wins = [value for value in outcomes if value > 0]
        losses = [value for value in outcomes if value < 0]

        profit_factor = None
        if r_values and losses:
            profit_factor = sum(value for value in r_values if value > 0) / abs(
                sum(value for value in r_values if value < 0)
            )

        groups.append(
            {
                "key": key,
                "sample_size": len(items),
                "win_rate": (len(wins) / len(outcomes)) if outcomes else None,
                "average_r": (sum(r_values) / len(r_values)) if r_values else None,
                "median_r": median(r_values) if r_values else None,
                "net_pnl": sum(pnl_values) if pnl_values else None,
                "profit_factor": profit_factor,
            }
        )

    return {
        "filters": filters.__dict__,
        "group_by": group_by,
        "groups": groups,
    }
