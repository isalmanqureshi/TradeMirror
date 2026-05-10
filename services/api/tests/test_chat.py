from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models import JournalEntry, Trade, TradeContext
from app.schemas.chat import ChatFilters
from app.services.analytics import AnalyticsFilters
from app.services.chat.classifier import classify_intent
from app.services.chat.composer import compose_answer
from app.services.chat.orchestrator import handle_chat_message
from app.services.chat.retrieval import get_best_trades, get_trade_context_records


class FakeResult:
    def __init__(self, items: list):
        self._items = items

    def all(self) -> list:
        return self._items


class FakeDB:
    def __init__(self, trades: list[Trade], journals: list[JournalEntry]):
        self.trades = trades
        self.journals = journals

    def scalars(self, stmt):
        text = str(stmt)
        if "journal_entries" in text:
            return FakeResult(list(self.journals))
        return FakeResult(list(self.trades))

    def execute(self, stmt):
        rows = [(trade, trade.trade_context) for trade in self.trades if trade.trade_context is not None]
        limit = stmt._limit_clause.value if getattr(stmt, "_limit_clause", None) is not None else None
        if limit is not None:
            rows = rows[:limit]
        return FakeResult(rows)


def _trade(uid: UUID, r: Decimal | None = Decimal("1.0"), pnl: Decimal | None = Decimal("100"), with_context: bool = True) -> Trade:
    trade = Trade(
        id=uuid4(),
        user_id=uid,
        strategy_id=None,
        source_type="live",
        instrument="futures",
        symbol="NQ",
        side="long",
        entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        entry_price=Decimal("1"),
        pnl=pnl,
        r_multiple=r,
        order_type="market",
        session_label="ny",
    )
    if with_context:
        trade.trade_context = TradeContext(
            trade_id=trade.id,
            trend_regime="up",
            volatility_regime="high",
            macro_event_nearby=True,
            macro_event_name="CPI",
            minutes_to_event=15,
        )
    return trade


def test_classifier_routes_performance_phrase() -> None:
    assert classify_intent("How did my NQ strategy perform?").primary_intent == "performance_summary"


def test_classifier_risk_drift_and_backtest_live_paths() -> None:
    assert classify_intent("How has my risk drift changed?").primary_intent == "risk_drift"
    assert classify_intent("How did my risk change over time?").primary_intent == "risk_drift"
    assert classify_intent("Is my live trading drifting from the backtest?").primary_intent == "backtest_live_comparison"


def test_analytics_sample_size_from_grouped_payloads() -> None:
    regime = compose_answer("regime_analysis", {"groups": [{"sample_size": 3}, {"sample_size": 4}]}, [], [], [])
    execution = compose_answer("execution_quality", {"groups": [{"sample_size": 2}, {"sample_size": 4}]}, [], [], [])
    comparison = compose_answer("backtest_live_comparison", {"backtest_sample_size": 4, "live_sample_size": 3}, [], [], [])
    assert "not enough matching trades" not in regime.lower()
    assert "not enough matching trades" not in execution.lower()
    assert "not enough matching trades" not in comparison.lower()


def test_trade_context_lookup_uses_joined_context_rows_with_limit() -> None:
    uid = uuid4()
    trades = [_trade(uid, with_context=False) for _ in range(5)] + [_trade(uid, with_context=True) for _ in range(3)]
    db = FakeDB(trades, [])
    filters = AnalyticsFilters(user_id=uid)

    results = get_trade_context_records(db, uid, filters, limit=2)
    assert len(results) == 2


def test_direct_advice_request_refused() -> None:
    uid = uuid4()
    db = FakeDB([], [])
    response = handle_chat_message(db, uid, "Should I buy NQ now?", ChatFilters())
    assert "cannot tell you whether to buy" in response.answer.lower()


def test_evidence_keys_always_present() -> None:
    uid = uuid4()
    db = FakeDB([], [])
    response = handle_chat_message(db, uid, "What is the weather?", ChatFilters())
    assert set(response.evidence.model_dump().keys()) == {"analytics", "trades", "journal_entries", "trade_context"}


def test_chat_route_accepts_demo_user_header() -> None:
    uid = uuid4()
    trades = [_trade(uid, Decimal("1"), Decimal("50")) for _ in range(6)]
    db = FakeDB(trades, [])

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.post(
        "/chat",
        json={"message": "How did my NQ strategy perform?"},
        headers={"X-Demo-User-Id": str(uid)},
    )
    assert response.status_code == 200
    assert set(response.json()["evidence"].keys()) == {"analytics", "trades", "journal_entries", "trade_context"}
    app.dependency_overrides.clear()


def test_get_best_trades_query_excludes_double_null_and_uses_nulls_last() -> None:
    class CaptureDB:
        def __init__(self):
            self.stmt = None

        def scalars(self, stmt):
            self.stmt = stmt
            return FakeResult([])

    uid = uuid4()
    db = CaptureDB()
    filters = AnalyticsFilters(user_id=uid)
    get_best_trades(db, uid, filters, limit=10)

    compiled = str(db.stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "r_multiple IS NOT NULL OR trades.pnl IS NOT NULL" in compiled
    assert "NULLS LAST" in compiled
