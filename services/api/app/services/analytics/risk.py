from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Trade
from app.services.analytics.filters import AnalyticsFilters, apply_trade_filters

def get_risk_drift(db: Session, filters: AnalyticsFilters) -> dict:
    trades = db.scalars(apply_trade_filters(select(Trade), filters)).all()
    risk = [t for t in trades if t.planned_risk is not None and t.actual_risk is not None]
    deltas = [float(t.actual_risk - t.planned_risk) for t in risk]
    delta_pct = [float((t.actual_risk - t.planned_risk) / t.planned_risk) for t in risk if float(t.planned_risk) != 0]
    oversized = [t for t in risk if float(t.actual_risk) > float(t.planned_risk) * 1.25]
    return {"filters": filters.__dict__, "sample_size": len(trades), "risk_sample_size": len(risk), "planned_risk_avg": (sum(float(t.planned_risk) for t in risk)/len(risk)) if risk else None, "actual_risk_avg": (sum(float(t.actual_risk) for t in risk)/len(risk)) if risk else None, "average_risk_delta": (sum(deltas)/len(deltas)) if deltas else None, "average_risk_delta_pct": (sum(delta_pct)/len(delta_pct)) if delta_pct else None, "max_actual_risk": max((float(t.actual_risk) for t in risk), default=None), "oversized_trade_count": len(oversized), "oversized_trade_rate": (len(oversized)/len(risk)) if risk else None}
