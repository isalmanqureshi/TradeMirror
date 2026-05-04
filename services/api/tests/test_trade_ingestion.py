from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.ingestion import trade_ingestion


class FakeDB:
    def __init__(self) -> None:
        self.added = []
        self.committed = False
        self._duplicate_checks = 0
        self.duplicate_on_second = False

    def scalar(self, _statement):
        self._duplicate_checks += 1
        if self.duplicate_on_second and self._duplicate_checks == 2:
            return object()
        return None

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        return None

    def commit(self):
        self.committed = True


def _upload(csv_text: str):
    return SimpleNamespace(file=BytesIO(csv_text.encode("utf-8")))


@pytest.fixture(autouse=True)
def _patch_resolvers(monkeypatch):
    strategy = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(trade_ingestion, "_resolve_user", lambda db, user_id: uuid4())
    monkeypatch.setattr(trade_ingestion, "_resolve_strategy", lambda db, user_id, strategy_name, instrument: strategy)


def test_valid_csv_inserts_trades():
    db = FakeDB()
    csv_text = "symbol,side,entry_time,entry_price\nNQ,long,2024-01-01 09:30:00,16000\n"

    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, None, "Breakout", "live")

    assert result["total_rows"] == 1
    assert result["inserted"] == 1
    assert result["skipped"] == 0
    assert result["errors"] == []


def test_missing_required_column_returns_error():
    db = FakeDB()
    csv_text = "symbol,side,entry_time\nNQ,long,2024-01-01 09:30:00\n"

    with pytest.raises(ValueError, match="missing required columns"):
        trade_ingestion.ingest_trade_csv(_upload(csv_text), db, None, "Breakout", "live")


def test_invalid_rows_partial_success():
    db = FakeDB()
    csv_text = "symbol,side,entry_time,entry_price\nNQ,long,2024-01-01 09:30:00,16000\nES,bad,2024-01-01 10:00:00,5300\n"

    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, None, "Breakout", "live")

    assert result["inserted"] == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["row_number"] == 3


def test_duplicate_rows_are_skipped():
    db = FakeDB()
    db.duplicate_on_second = True
    csv_text = (
        "symbol,side,entry_time,entry_price\n"
        "NQ,long,2024-01-01 09:30:00,16000\n"
        "NQ,long,2024-01-01 09:30:00,16000\n"
    )

    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, None, "Breakout", "live")

    assert result["inserted"] == 1
    assert result["skipped"] == 1


def test_journal_note_creates_journal_entry():
    db = FakeDB()
    csv_text = "symbol,side,entry_time,entry_price,journal_note\nNQ,long,2024-01-01 09:30:00,16000,Good trade\n"

    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, None, "Breakout", "paper")

    assert result["inserted"] == 1
    assert len(db.added) == 2


def test_column_alias_mapping_and_datetime_parsing():
    db = FakeDB()
    csv_text = "symbol,side,entry time,EntryPrice,P&L\nBTC,short,2024-01-02T12:00:00,40000,500\n"

    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, None, "Reversal", "backtest")

    assert result["inserted"] == 1
    assert result["errors"] == []
