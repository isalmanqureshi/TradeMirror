from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.ingestion import trade_ingestion


class FakeDB:
    def __init__(self) -> None:
        self.added = []
        self.committed = False
        self.integrity_error_on_flush = False

    def scalar(self, _statement):
        return None

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, objs):
        self.added.extend(objs)

    def flush(self):
        if self.integrity_error_on_flush:
            from sqlalchemy.exc import IntegrityError

            raise IntegrityError("dup", {}, None)
        return None

    def rollback(self):
        return None

    def commit(self):
        self.committed = True


def _upload(csv_text: str):
    return SimpleNamespace(file=BytesIO(csv_text.encode("utf-8")))


@pytest.fixture(autouse=True)
def _patch_strategy(monkeypatch):
    strategy = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(trade_ingestion, "_resolve_strategy", lambda db, user_id, strategy_name, instrument: strategy)


def test_timezone_aware_normalizes_to_utc():
    db = FakeDB()
    csv_text = "symbol,side,entry_time,entry_price\nNQ,long,2024-01-01T09:30:00-05:00,16000\n"
    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, uuid4(), "Breakout", "live")
    assert result["inserted"] == 1
    trade = db.added[0]
    assert trade.entry_time.isoformat() == "2024-01-01T14:30:00+00:00"


def test_naive_datetime_rejected():
    db = FakeDB()
    csv_text = "symbol,side,entry_time,entry_price\nNQ,long,2024-01-01 09:30:00,16000\n"
    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, uuid4(), "Breakout", "live")
    assert result["inserted"] == 0
    assert result["errors"][0]["code"] == "naive_datetime_not_allowed"


def test_equivalent_offsets_duplicate_in_batch():
    db = FakeDB()
    csv_text = (
        "symbol,side,entry_time,entry_price\n"
        "NQ,long,2024-01-01T09:30:00-05:00,16000\n"
        "NQ,long,2024-01-01T14:30:00+00:00,16000\n"
    )
    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, uuid4(), "Breakout", "live")
    assert result["inserted"] == 1
    assert result["skipped"] == 1
    assert any(e["code"] == "duplicate_trade" for e in result["errors"])


def test_invalid_json_setup_tags_code():
    db = FakeDB()
    csv_text = "symbol,side,entry_time,entry_price,setup_tags\nNQ,long,2024-01-01T09:30:00Z,16000,{bad\n"
    result = trade_ingestion.ingest_trade_csv(_upload(csv_text), db, uuid4(), "Breakout", "paper")
    assert result["inserted"] == 0
    assert result["errors"][0]["code"] == "invalid_json"


def test_file_too_large_rejected():
    db = FakeDB()
    large = "a" * (trade_ingestion.MAX_UPLOAD_SIZE_BYTES + 10)
    with pytest.raises(ValueError, match="file_too_large"):
        trade_ingestion.ingest_trade_csv(SimpleNamespace(file=BytesIO(large.encode())), db, uuid4(), "Breakout", "live")
