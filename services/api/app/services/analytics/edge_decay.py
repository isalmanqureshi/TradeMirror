from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters

def get_edge_decay(db: Session, filters: AnalyticsFilters, window_size: int = 20) -> dict:
    trades = [t for t in db.scalars(apply_trade_filters(select(Trade).order_by(Trade.entry_time), filters)).all() if t.r_multiple is not None]
    if len(trades) < window_size:
        return {"filters": filters.__dict__, "window_size": window_size, "sample_size": len(trades), "points": [], "message": "Insufficient trades for requested window size"}
    pts=[]
    for i in range(window_size-1, len(trades)):
        window=trades[i-window_size+1:i+1]
        r=[float(t.r_multiple) for t in window]
        wins=[v for v in r if v>0]
        losses=[v for v in r if v<0]
        pf=(sum(wins)/abs(sum(losses))) if losses else None
        pts.append({"entry_time": trades[i].entry_time, "trade_id": str(trades[i].id), "rolling_average_r": sum(r)/len(r), "rolling_win_rate": len(wins)/len(r), "rolling_profit_factor": pf, "rolling_expectancy_r": sum(r)/len(r), "sample_size": window_size})
    return {"filters": filters.__dict__, "window_size": window_size, "sample_size": len(trades), "points": pts, "message": None}
