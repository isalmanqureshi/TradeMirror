from __future__ import annotations

from collections import defaultdict
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def get_execution_quality(db: Session, filters: AnalyticsFilters, group_by: str) -> dict:
    trades = db.scalars(apply_trade_filters(select(Trade), filters)).all()

    grouped: dict[str, list[Trade]] = defaultdict(list)
    for trade in trades:
        key = (
            getattr(trade, group_by, None)
            or getattr(getattr(trade, "trade_context", None), group_by, None)
            or "unknown"
        )
        grouped[str(key)].append(trade)

    rows: list[dict] = []
    for key, items in grouped.items():
        slippage_values = [float(item.slippage) for item in items if item.slippage is not None]
        fees_values = [float(item.fees) for item in items if item.fees is not None]
        pnl_values = [float(item.pnl) for item in items if item.pnl is not None]
        r_values = [float(item.r_multiple) for item in items if item.r_multiple is not None]

        rows.append(
            {
                "key": key,
                "sample_size": len(items),
                "average_slippage": (
                    (sum(slippage_values) / len(slippage_values)) if slippage_values else None
                ),
                "median_slippage": median(slippage_values) if slippage_values else None,
                "max_slippage": max(slippage_values) if slippage_values else None,
                "slippage_sample_size": len(slippage_values),
                "average_fees": (sum(fees_values) / len(fees_values)) if fees_values else None,
                "total_fees": sum(fees_values) if fees_values else None,
                "average_pnl": (sum(pnl_values) / len(pnl_values)) if pnl_values else None,
                "average_r": (sum(r_values) / len(r_values)) if r_values else None,
            }
        )

    return {"filters": filters.__dict__, "group_by": group_by, "groups": rows}
