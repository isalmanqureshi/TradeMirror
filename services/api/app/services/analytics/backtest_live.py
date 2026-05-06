from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters

def compare_backtest_live(db: Session, filters: AnalyticsFilters) -> dict:
    trades=[t for t in db.scalars(apply_trade_filters(select(Trade), filters)).all() if t.r_multiple is not None]
    b=[float(t.r_multiple) for t in trades if t.source_type=='backtest']
    l=[float(t.r_multiple) for t in trades if t.source_type=='live']
    if len(b)<5 or len(l)<5:
        return {"filters": filters.__dict__, "status":"insufficient_data", "backtest_sample_size":len(b), "live_sample_size":len(l), "ks_test":None, "message":"Insufficient sample sizes: require backtest>=5 and live>=5"}
    bavg=sum(b)/len(b); lavg=sum(l)/len(l)
    bwr=len([v for v in b if v>0])/len(b); lwr=len([v for v in l if v>0])/len(l)
    return {"filters": filters.__dict__,"status":"ok","backtest_sample_size":len(b),"live_sample_size":len(l),"backtest_average_r":bavg,"live_average_r":lavg,"backtest_win_rate":bwr,"live_win_rate":lwr,"expectancy_delta":lavg-bavg,"average_r_delta":lavg-bavg,"win_rate_delta":lwr-bwr,"ks_test":None,"message":"Statistical test not available in this phase"}
