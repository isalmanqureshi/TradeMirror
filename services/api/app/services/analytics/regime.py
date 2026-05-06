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
    for t in trades:
        key = getattr(t.trade_context, group_by, None) if group_by in CONTEXT_FIELDS else getattr(t, group_by, None)
        grouped[str(key).lower() if key is not None else "unknown"].append(t)
    groups = []
    for key, items in grouped.items():
        r = [float(i.r_multiple) for i in items if i.r_multiple is not None]
        pnl = [float(i.pnl) for i in items if i.pnl is not None]
        wins = [v for v in (r if r else pnl) if v > 0]
        losses = [v for v in (r if r else pnl) if v < 0]
        pf = (sum(v for v in r if v > 0) / abs(sum(v for v in r if v < 0))) if r and losses else None
        groups.append({"key": key, "sample_size": len(items), "win_rate": (len(wins)/len(r if r else pnl)) if (r or pnl) else None, "average_r": (sum(r)/len(r)) if r else None, "median_r": median(r) if r else None, "net_pnl": sum(pnl) if pnl else None, "profit_factor": pf})
    return {"filters": filters.__dict__, "group_by": group_by, "groups": groups}
