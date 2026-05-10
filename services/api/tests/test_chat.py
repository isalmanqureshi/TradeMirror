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
from app.services.chat.composer import INTENT_SUGGESTIONS, build_warnings, compose_answer
from app.services.chat.orchestrator import handle_chat_message
from app.services.chat.retrieval import get_best_trades, get_trade_context_records


class FakeResult:
    def __init__(self, items: list): self._items = items
    def all(self) -> list: return self._items


class FakeDB:
    def __init__(self, trades: list[Trade], journals: list[JournalEntry]): self.trades = trades; self.journals = journals
    def scalars(self, stmt): return FakeResult(list(self.journals) if "journal_entries" in str(stmt) else list(self.trades))
    def execute(self, stmt):
        rows = [(trade, trade.trade_context) for trade in self.trades if trade.trade_context is not None]
        limit = stmt._limit_clause.value if getattr(stmt, "_limit_clause", None) is not None else None
        return FakeResult(rows[:limit] if limit is not None else rows)


def _trade(uid: UUID, r: Decimal | None = Decimal("1.0"), pnl: Decimal | None = Decimal("100"), with_context: bool = True) -> Trade:
    trade = Trade(id=uuid4(), user_id=uid, strategy_id=None, source_type="live", instrument="futures", symbol="NQ", side="long", entry_time=datetime(2024, 1, 1, tzinfo=timezone.utc), entry_price=Decimal("1"), pnl=pnl, r_multiple=r, order_type="market", session_label="ny")
    if with_context:
        trade.trade_context = TradeContext(trade_id=trade.id, trend_regime="up", volatility_regime="high", atr_percentile=Decimal("0.8"), realized_vol_percentile=Decimal("0.7"), macro_event_nearby=True, macro_event_name="CPI", minutes_to_event=15)
    return trade


def test_classifier_realistic_phrasing() -> None:
    assert classify_intent("What is my win rate this month?").primary_intent == "performance_summary"
    assert classify_intent("Which session has the worst slippage?").primary_intent == "execution_quality"
    assert classify_intent("Is my backtest still valid?").primary_intent == "backtest_live_comparison"
    assert classify_intent("Show high ATR trades.").primary_intent in {"trade_context_lookup", "trade_lookup"}


def test_response_shape_and_metadata() -> None:
    uid = uuid4(); db = FakeDB([], [])
    response = handle_chat_message(db, uid, "How did my NQ strategy perform?", ChatFilters())
    assert response.answer and response.intent and response.evidence
    assert response.metadata is not None
    assert response.metadata.evidence_counts.trades == len(response.evidence.trades)


def test_small_sample_warning() -> None:
    warnings = build_warnings("performance_summary", {}, [], [], 4)
    assert any("Sample size is small" in w for w in warnings)


def test_context_and_journal_no_insufficient_phrase() -> None:
    answer_j = compose_answer("journal_lookup", {}, [], [{"journal_entry_id": uuid4(), "text_excerpt": "a"}], [], warnings=[])
    answer_c = compose_answer("trade_context_lookup", {}, [], [], [{"trade_id": uuid4()}], warnings=[])
    assert "not enough matching trades" not in answer_j.lower()
    assert "not enough matching trades" not in answer_c.lower()


def test_trade_context_lookup_uses_joined_context_rows_with_limit() -> None:
    uid = uuid4(); trades = [_trade(uid, with_context=False) for _ in range(5)] + [_trade(uid, with_context=True) for _ in range(3)]
    results = get_trade_context_records(FakeDB(trades, []), uid, AnalyticsFilters(user_id=uid), limit=2)
    assert len(results) == 2


def test_direct_advice_request_refused_and_safe() -> None:
    response = handle_chat_message(FakeDB([], []), uuid4(), "Should I buy NQ now?", ChatFilters())
    assert "cannot tell you whether to buy" in response.answer.lower()
    assert "historical trades" in response.answer.lower()


def test_no_prohibited_direct_trading_phrases() -> None:
    answer = compose_answer("unknown", {}, [], [], [], warnings=[]).lower()
    for phrase in ["you should buy", "you should sell", "enter now", "short now", "take the trade", "use leverage"]:
        assert phrase not in answer


def test_suggested_questions_match_intent() -> None:
    resp = handle_chat_message(FakeDB([], []), uuid4(), "Which session has the worst slippage?", ChatFilters())
    assert resp.suggested_questions == INTENT_SUGGESTIONS["execution_quality"]


def test_chat_route_json_serializable() -> None:
    uid = uuid4(); db = FakeDB([_trade(uid, Decimal("1"), Decimal("50")) for _ in range(6)], [])
    app.dependency_overrides[get_db] = lambda: db
    response = TestClient(app).post("/chat", json={"message": "How did my NQ strategy perform?"}, headers={"X-Demo-User-Id": str(uid)})
    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["evidence_counts"]["trades"] >= 0


def test_get_best_trades_query_excludes_double_null_and_uses_nulls_last() -> None:
    class CaptureDB:
        def __init__(self): self.stmt = None
        def scalars(self, stmt): self.stmt = stmt; return FakeResult([])
    db = CaptureDB(); get_best_trades(db, uuid4(), AnalyticsFilters(user_id=uuid4()), limit=10)
    compiled = str(db.stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "IS NOT NULL OR trades.pnl IS NOT NULL" in compiled and "NULLS LAST" in compiled
