from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models import JournalEntry, Trade, TradeContext
from app.schemas.chat import ChatFilters
from app.services.chat.classifier import classify_intent
from app.services.chat.orchestrator import handle_chat_message


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


def _trade(uid: UUID, r: Decimal = Decimal("1.0"), pnl: Decimal = Decimal("100")) -> Trade:
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


def test_classifier_routes_other_intents() -> None:
    assert classify_intent("Which volatility regime hurt me most?").primary_intent == "regime_analysis"
    assert classify_intent("Which session has the worst slippage?").primary_intent == "execution_quality"
    assert classify_intent("Is my live trading drifting from the backtest?").primary_intent == "backtest_live_comparison"


def test_direct_advice_request_refused() -> None:
    uid = uuid4()
    db = FakeDB([], [])
    response = handle_chat_message(db, uid, "Should I buy NQ now?", ChatFilters())
    assert "cannot tell you whether to buy" in response.answer.lower()


def test_journal_lookup_sample_size_uses_journal_entries() -> None:
    uid = uuid4()
    journal = JournalEntry(
        id=uuid4(),
        user_id=uid,
        trade_id=None,
        strategy_id=None,
        entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        title="Review",
        text="Emotion and mistake notes",
    )
    db = FakeDB([], [journal, journal, journal])
    response = handle_chat_message(db, uid, "journal review", ChatFilters())
    assert "matching journal entries" in response.answer.lower()
    assert "matching trades" not in response.answer.lower()


def test_trade_context_lookup_sample_size_uses_context_records() -> None:
    uid = uuid4()
    trades = [_trade(uid) for _ in range(3)]
    db = FakeDB(trades, [])
    response = handle_chat_message(db, uid, "show context by session", ChatFilters())
    assert response.intent == "trade_context_lookup"
    assert "matching trade context records" in response.answer.lower()
    assert "matching trades" not in response.answer.lower()


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
