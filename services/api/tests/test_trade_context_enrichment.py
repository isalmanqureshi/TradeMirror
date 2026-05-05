from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.api.routes.enrichment import (
    enrich_context_batch,
    enrich_single_trade,
    get_trade_context,
)
from app.models import Trade, TradeContext
from app.services.enrichment.trade_context_enrichment import (
    batch_enrich_trade_context,
    enrich_trade_context,
)


class FakeMarketProvider:
    def __init__(self, atr=None, rv=None, trend=None, snapshot=None):
        self.atr = atr
        self.rv = rv
        self.trend = trend
        self.snapshot = snapshot or {}

    def get_snapshot(self, symbol, timestamp):
        return self.snapshot

    def get_atr_percentile(self, symbol, timestamp):
        return self.atr

    def get_realized_vol_percentile(self, symbol, timestamp):
        return self.rv

    def get_trend_inputs(self, symbol, timestamp):
        return self.trend


class FakeEventProvider:
    def __init__(self, minutes=15, name="CPI"):
        self.minutes = minutes
        self.name = name

    def get_nearest_event(self, timestamp, symbol=None):
        return {"timestamp": timestamp + timedelta(minutes=self.minutes), "name": self.name}


class FakeDB:
    def __init__(self, trades=None):
        self.trades = {t.id: t for t in (trades or [])}
        self.contexts = {}

    def scalar(self, stmt):
        model = stmt.column_descriptions[0].get("entity")
        where = list(stmt._where_criteria)
        rhs = where[0].right.value if where else None
        if model is Trade:
            return self.trades.get(rhs)
        if model is TradeContext:
            return self.contexts.get(rhs)
        return None

    def scalars(self, stmt):
        desc = stmt.column_descriptions[0]
        entity = desc.get("entity")
        expr = desc.get("expr")

        if entity is Trade:
            items = list(self.trades.values())
            if stmt._limit_clause is not None:
                items = items[: stmt._limit_clause.value]
            return type("S", (), {"all": lambda self: items})()

        if expr is not None and str(expr).endswith("trade_context.trade_id"):
            values = list(self.contexts.keys())
            return type("S", (), {"all": lambda self: values})()

        return type("S", (), {"all": lambda self: []})()

    def add(self, obj):
        if isinstance(obj, TradeContext):
            self.contexts[obj.trade_id] = obj

    def flush(self):
        return None

    def commit(self):
        return None


def _trade(hour=14, exit_minutes=24):
    entry = datetime(2024, 1, 1, hour, 0, tzinfo=timezone.utc)
    exit_time = entry + timedelta(minutes=exit_minutes) if exit_minutes is not None else None
    return Trade(
        id=uuid4(),
        user_id=uuid4(),
        strategy_id=None,
        source_type="live",
        instrument="futures",
        symbol="NQ",
        side="long",
        entry_time=entry,
        exit_time=exit_time,
        entry_price=Decimal("1"),
    )


def test_single_trade_enrich_creates_row():
    trade = _trade()
    db = FakeDB([trade])

    context = enrich_trade_context(db, trade.id)

    assert context.trade_id == trade.id


def test_reenrich_updates_no_duplicate():
    trade = _trade()
    db = FakeDB([trade])

    enrich_trade_context(db, trade.id, market_data_provider=FakeMarketProvider(atr=20))
    enrich_trade_context(db, trade.id, market_data_provider=FakeMarketProvider(atr=90))

    assert len(db.contexts) == 1
    assert db.contexts[trade.id].volatility_regime == "high"


def test_session_windows_and_holding_minutes():
    trade = _trade(hour=8, exit_minutes=60)
    db = FakeDB([trade])

    context = enrich_trade_context(db, trade.id)

    assert context.context_payload["session_label"] == "london"
    assert context.context_payload["holding_minutes"] == 60


def test_atr_mapping_and_trend_mapping():
    trade = _trade()
    db = FakeDB([trade])
    provider = FakeMarketProvider(
        atr=50,
        rv=85,
        trend={"close": 100, "ma_50": 100, "ma_50_slope": 0},
    )

    context = enrich_trade_context(db, trade.id, market_data_provider=provider)

    assert context.volatility_regime == "medium"
    assert context.trend_regime == "volatile"


def test_missing_market_data_null_safe_and_marked():
    trade = _trade(exit_minutes=None)
    db = FakeDB([trade])

    context = enrich_trade_context(db, trade.id)

    assert context.atr_percentile is None and context.trend_regime is None
    assert context.context_payload["market_data_available"] is False
    assert context.context_payload["event_data_available"] is False


def test_event_proximity():
    trade = _trade()
    db = FakeDB([trade])

    context = enrich_trade_context(db, trade.id, event_provider=FakeEventProvider(minutes=30))

    assert context.macro_event_nearby is True
    assert context.macro_event_name == "CPI"
    assert context.minutes_to_event == 30


def test_batch_summary_counts_and_idempotent():
    t1, t2 = _trade(), _trade(hour=22)
    db = FakeDB([t1, t2])

    summary = batch_enrich_trade_context(db, limit=2)
    summary2 = batch_enrich_trade_context(db, limit=2, skip_existing=True)

    assert summary.processed == 2
    assert summary.enriched == 2
    assert len(db.contexts) == 2
    assert summary2.skipped == 2


def test_get_trade_context_returns_stored_context():
    trade = _trade()
    db = FakeDB([trade])
    enrich_trade_context(db, trade.id)

    assert get_trade_context(trade.id, db).trade_id == trade.id


def test_routes_use_injected_providers():
    trade = _trade()
    db = FakeDB([trade])
    provider = FakeMarketProvider(atr=80)
    event_provider = FakeEventProvider(minutes=10)

    single = enrich_single_trade(trade.id, db, provider, event_provider)
    summary = enrich_context_batch(
        db=db,
        market_data_provider=provider,
        event_provider=event_provider,
    )

    assert single.volatility_regime == "high"
    assert summary.enriched == 1
