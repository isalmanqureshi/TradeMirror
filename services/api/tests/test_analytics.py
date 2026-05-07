from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

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
            items.sort(key=lambda trade: trade.entry_time)
        return type("S", (), {"all": lambda self: items})()


def _trade(
    idx: int,
    user_id,
    source_type="live",
    r=None,
    pnl=None,
    slip=None,
    planned=None,
    actual=None,
    vol="high",
):
    trade = Trade(
        id=uuid4(),
        user_id=user_id,
        strategy_id=None,
        source_type=source_type,
        instrument="futures",
        symbol="NQ",
        side="long",
        entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=idx),
        entry_price=Decimal("1"),
        r_multiple=r,
        pnl=pnl,
        slippage=slip,
        planned_risk=planned,
        actual_risk=actual,
        fees=Decimal("1"),
        order_type="market",
        session_label="ny",
    )
    trade.trade_context = TradeContext(
        trade_id=trade.id,
        volatility_regime=vol,
        trend_regime="up",
        macro_event_nearby=None,
    )
    return trade


def test_analytics_services_and_endpoints() -> None:
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

    summary = get_performance_summary(db, filters)
    assert summary["sample_size"] == 5
    assert summary["average_r"] is not None

    grouped = get_regime_sensitivity(db, filters, "volatility_regime")
    assert any(group["key"] == "unknown" for group in grouped["groups"])

    execution = get_execution_quality(db, filters, "session_label")["groups"][0]
    assert execution["slippage_sample_size"] == 3

    risk = get_risk_drift(db, filters)
    assert risk["oversized_trade_rate"] == 0.5

    assert get_edge_decay(db, filters, window_size=20)["points"] == []
    assert len(get_edge_decay(db, filters, window_size=2)["points"]) >= 1

    assert compare_backtest_live(db, filters)["status"] == "insufficient_data"

    more_trades = trades + [
        _trade(10 + i, uid, "backtest", Decimal("1"), Decimal("10")) for i in range(4)
    ] + [_trade(20 + i, uid, "live", Decimal("0.5"), Decimal("5")) for i in range(3)]
    ok = compare_backtest_live(FakeDB(more_trades), filters)
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
    for endpoint in endpoints:
        response = client.get(endpoint, params={"user_id": str(uid)})
        assert response.status_code == 200
        assert "filters" in response.json()
    app.dependency_overrides.clear()
