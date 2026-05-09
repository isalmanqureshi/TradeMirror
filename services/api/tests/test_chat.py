from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models import JournalEntry, Trade, TradeContext
from app.schemas.chat import ChatFilters
from app.services.chat.classifier import classify_intent
from app.services.chat.orchestrator import handle_chat_message


class FakeResult:
    def __init__(self, items):
        self._items = items

    def all(self):
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


def _trade(uid, r=Decimal("1.0"), pnl=Decimal("100")):
    trade = Trade(id=uuid4(), user_id=uid, strategy_id=None, source_type="live", instrument="futures", symbol="NQ", side="long", entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc), entry_price=Decimal("1"), pnl=pnl, r_multiple=r, order_type="market", session_label="ny")
    trade.trade_context = TradeContext(trade_id=trade.id, trend_regime="up", volatility_regime="high", macro_event_nearby=True, macro_event_name="CPI", minutes_to_event=15)
    return trade


def test_classifier_routes():
    assert classify_intent("How did my NQ strategy perform?").primary_intent == "performance_summary"
    assert classify_intent("Which volatility regime hurt me most?").primary_intent == "regime_analysis"
    assert classify_intent("Which session has the worst slippage?").primary_intent == "execution_quality"
    assert classify_intent("Is my live trading drifting from the backtest?").primary_intent == "backtest_live_comparison"


def test_chat_orchestration_and_api():
    uid = uuid4()
    trades = [_trade(uid, Decimal("1"), Decimal("50")) for _ in range(6)]
    journal = JournalEntry(id=uuid4(), user_id=uid, trade_id=trades[0].id, strategy_id=None, entry_time=trades[0].entry_time, title="Review", text="Emotion and mistake notes")
    db = FakeDB(trades, [journal])

    assert handle_chat_message(db, uid, "What is the weather?", ChatFilters()).intent == "unknown"
    assert "cannot tell you whether to buy" in handle_chat_message(db, uid, "Should I buy NQ now?", ChatFilters()).answer.lower()
    assert "analytics" in handle_chat_message(db, uid, "How did performance look?", ChatFilters()).evidence.model_dump()
    assert handle_chat_message(db, uid, "show trades", ChatFilters()).evidence.trades[0].trade_id
    assert handle_chat_message(db, uid, "journal review", ChatFilters()).evidence.journal_entries
    assert "not enough matching trades" in handle_chat_message(FakeDB(trades[:3], []), uid, "how did I do", ChatFilters()).answer.lower()

    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    response = client.post("/chat", json={"message": "How did my NQ strategy perform?"})
    assert response.status_code == 200
    assert set(response.json()["evidence"].keys()) == {"analytics", "trades", "journal_entries", "trade_context"}
    app.dependency_overrides.clear()
