from __future__ import annotations
from collections import defaultdict
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters


def get_execution_quality(db: Session, filters: AnalyticsFilters, group_by: str) -> dict:
    trades = db.scalars(apply_trade_filters(select(Trade), filters)).all()
    grouped = defaultdict(list)
    for t in trades:
        grouped[str(getattr(t, group_by, None) or getattr(getattr(t,'trade_context',None),group_by,None) or 'unknown')].append(t)
    rows=[]
    for key,items in grouped.items():
        slip=[float(i.slippage) for i in items if i.slippage is not None]
        fees=[float(i.fees) for i in items if i.fees is not None]
        pnl=[float(i.pnl) for i in items if i.pnl is not None]
        r=[float(i.r_multiple) for i in items if i.r_multiple is not None]
        rows.append({"key":key,"sample_size":len(items),"average_slippage":(sum(slip)/len(slip)) if slip else None,"median_slippage":median(slip) if slip else None,"max_slippage":max(slip) if slip else None,"slippage_sample_size":len(slip),"average_fees":(sum(fees)/len(fees)) if fees else None,"total_fees":sum(fees) if fees else None,"average_pnl":(sum(pnl)/len(pnl)) if pnl else None,"average_r":(sum(r)/len(r)) if r else None})
    return {"filters": filters.__dict__, "group_by": group_by, "groups": rows}
