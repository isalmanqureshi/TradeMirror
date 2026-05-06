from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_db
from app.main import app
from app.models import Trade, TradeContext
from app.services.analytics import (
    AnalyticsFilters,
    compare_backtest_live,
    get_edge_decay,
    get_execution_quality,
    get_performance_summary,
    get_regime_sensitivity,
    get_risk_drift,
)


class FakeDB:
    def __init__(self, trades: list[Trade]):
        self.trades = trades

    def scalars(self, stmt):
        items = list(self.trades)
        if hasattr(stmt, "_order_by_clauses") and stmt._order_by_clauses:
            items.sort(key=lambda t: t.entry_time)
        return type("S", (), {"all": lambda self: items})()


def _trade(i: int, user_id, source_type="live", r=None, pnl=None, slip=None, planned=None, actual=None, vol="high"):
    t = Trade(
        id=uuid4(), user_id=user_id, strategy_id=None, source_type=source_type, instrument="futures", symbol="NQ", side="long",
        entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=i), entry_price=Decimal("1"), r_multiple=r, pnl=pnl,
        slippage=slip, planned_risk=planned, actual_risk=actual, fees=Decimal("1"), order_type="market", session_label="ny"
    )
    t.trade_context = TradeContext(trade_id=t.id, volatility_regime=vol, trend_regime="up", macro_event_nearby=None)
    return t


def test_analytics_services_and_endpoints():
    uid = uuid4()
    trades = [
        _trade(1, uid, "live", Decimal("1"), Decimal("100"), Decimal("0.1"), Decimal("100"), Decimal("130"), "high"),
        _trade(2, uid, "live", Decimal("-0.5"), Decimal("-50"), None, Decimal("100"), Decimal("100"), None),
        _trade(3, uid, "backtest", Decimal("2"), Decimal("200"), Decimal("0.3"), Decimal("100"), Decimal("80"), "low"),
        _trade(4, uid, "backtest", Decimal("-1"), Decimal("-100"), Decimal("0.2"), Decimal("100"), Decimal("130"), "high"),
        _trade(5, uid, "live", None, None, None, None, None, "high"),
    ]
    db = FakeDB(trades)
    filters = AnalyticsFilters(user_id=uid)

    assert get_performance_summary(db, filters)["sample_size"] == 5
    assert get_performance_summary(db, filters)["average_r"] is not None
    assert any(g["key"] == "unknown" for g in get_regime_sensitivity(db, filters, "volatility_regime")["groups"])
    eq = get_execution_quality(db, filters, "session_label")["groups"][0]
    assert eq["slippage_sample_size"] == 3
    assert get_risk_drift(db, filters)["oversized_trade_rate"] == 0.5
    assert get_edge_decay(db, filters, window_size=20)["points"] == []
    assert len(get_edge_decay(db, filters, window_size=2)["points"]) >= 1
    assert compare_backtest_live(db, filters)["status"] == "insufficient_data"

    more = trades + [_trade(10 + i, uid, "backtest", Decimal("1"), Decimal("10")) for i in range(4)] + [_trade(20 + i, uid, "live", Decimal("0.5"), Decimal("5")) for i in range(3)]
    ok = compare_backtest_live(FakeDB(more), filters)
    assert ok["status"] == "ok"

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    endpoints = [
        "/analytics/summary",
        "/analytics/regime-sensitivity",
        "/analytics/execution-quality",
        "/analytics/risk-drift",
        "/analytics/edge-decay",
        "/analytics/backtest-live-comparison",
    ]
    for ep in endpoints:
        res = client.get(ep, params={"user_id": str(uid)})
        assert res.status_code == 200
        assert "filters" in res.json()
    app.dependency_overrides.clear()
