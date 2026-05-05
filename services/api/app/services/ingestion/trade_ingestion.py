import csv
import io
import json
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import JournalEntry, Strategy, Trade
from app.schemas.domain import SourceType, TradeSide

REQUIRED_COLUMNS = {"symbol", "side", "entry_time", "entry_price"}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_ROWS = 10_000
NUMERIC_FIELDS = {"entry_price", "exit_price", "quantity", "pnl", "r_multiple", "fees", "slippage", "planned_risk", "actual_risk"}
COLUMN_ALIASES = {"entry price": "entry_price", "entryprice": "entry_price", "p&l": "pnl"}


@dataclass
class RowError:
    row_number: int
    code: str
    field: str | None
    error: str


@dataclass
class ParsedTradeRow:
    row_number: int
    symbol: str
    side: str
    entry_time: datetime
    exit_time: datetime | None
    instrument: str
    numeric_values: dict[str, Decimal | None]
    order_type: str | None
    session_label: str | None
    setup_tags: list[str] | dict[str, object] | None
    journal_note: str | None


def _normalize_column(name: str) -> str:
    key = name.strip().lower().replace(" ", "_")
    return COLUMN_ALIASES.get(key, key)


def _parse_decimal(value: str | None, field: str) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid numeric value for {field}") from exc


def _parse_datetime(value: str | None, field: str) -> datetime | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid datetime for {field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"naive datetime is not allowed for {field}")
    return parsed.astimezone(timezone.utc)


def _infer_instrument(symbol: str | None) -> str:
    if not symbol:
        return "unknown"
    return "crypto" if "/" in symbol or symbol.upper().startswith("BTC") else "futures"


def _resolve_strategy(db: Session, user_id: uuid.UUID, strategy_name: str, instrument: str | None) -> Strategy:
    strategy = db.scalar(select(Strategy).where(Strategy.user_id == user_id, Strategy.name == strategy_name))
    if strategy is not None:
        return strategy
    strategy = Strategy(user_id=user_id, name=strategy_name, instrument=instrument)
    db.add(strategy)
    try:
        db.flush()
        return strategy
    except IntegrityError:
        db.rollback()
        return db.scalar(select(Strategy).where(Strategy.user_id == user_id, Strategy.name == strategy_name))


def _normalized_rows(file_bytes: bytes) -> tuple[list[str], Iterable[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(file_bytes.decode("utf-8-sig")))
    if reader.fieldnames is None:
        raise ValueError("CSV file is missing headers")
    reader.fieldnames = [_normalize_column(name) for name in reader.fieldnames]
    return reader.fieldnames, reader


def ingest_trade_csv(file: UploadFile, db: Session, user_id: uuid.UUID, strategy_name: str, source_type: str) -> dict:
    payload = file.file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(payload) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError("file_too_large")

    columns, rows = _normalized_rows(payload)
    missing = REQUIRED_COLUMNS - set(columns)
    if missing:
        raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")

    parsed_rows: list[ParsedTradeRow] = []
    errors: list[RowError] = []
    skipped = 0
    total_rows = 0

    for row_number, row in enumerate(rows, start=2):
        total_rows += 1
        if total_rows > MAX_UPLOAD_ROWS:
            raise ValueError("too_many_rows")
        try:
            symbol = (row.get("symbol") or "").strip()
            side = (row.get("side") or "").strip().lower()
            if not symbol:
                raise ValueError("symbol is required")
            if side not in {TradeSide.long.value, TradeSide.short.value}:
                errors.append(RowError(row_number, "invalid_side", "side", "side must be one of: long, short"))
                continue
            entry_time = _parse_datetime(row.get("entry_time"), "entry_time")
            if entry_time is None:
                raise ValueError("entry_time is required")
            entry_price = _parse_decimal(row.get("entry_price"), "entry_price")
            if entry_price is None:
                raise ValueError("entry_price is required")
            exit_time = _parse_datetime(row.get("exit_time"), "exit_time")
            if exit_time and exit_time < entry_time:
                raise ValueError("exit_time must be greater than or equal to entry_time")
            setup_tags = None
            setup_raw = row.get("setup_tags")
            if setup_raw and setup_raw.strip():
                try:
                    setup_tags = json.loads(setup_raw)
                except json.JSONDecodeError:
                    errors.append(RowError(row_number, "invalid_json", "setup_tags", "invalid json for setup_tags"))
                    continue
            numeric_values = {field: _parse_decimal(row.get(field), field) for field in NUMERIC_FIELDS}
            numeric_values["entry_price"] = entry_price
            parsed_rows.append(ParsedTradeRow(row_number, symbol, side, entry_time, exit_time, _infer_instrument(symbol), numeric_values, row.get("order_type") or None, row.get("session_label") or None, setup_tags, (row.get("journal_note") or "").strip() or None))
        except ValueError as exc:
            msg = str(exc)
            code = "invalid_datetime" if "datetime" in msg else "invalid_numeric" if "numeric" in msg else "naive_datetime_not_allowed" if "naive datetime" in msg else "invalid_row"
            field = "entry_time" if "entry_time" in msg else "exit_time" if "exit_time" in msg else None
            errors.append(RowError(row_number, code, field, msg))

    inserted = 0
    journal_entries: list[JournalEntry] = []
    strategy_cache: dict[str, Strategy] = {}
    seen_keys: set[tuple[uuid.UUID, str, str, datetime]] = set()

    for record in parsed_rows:
        strategy = strategy_cache.get(strategy_name)
        if strategy is None:
            strategy = _resolve_strategy(db, user_id, strategy_name, record.instrument)
            strategy_cache[strategy_name] = strategy
        dedupe_key = (strategy.id, record.symbol, record.side, record.entry_time)
        if dedupe_key in seen_keys:
            skipped += 1
            errors.append(RowError(record.row_number, "duplicate_trade", None, "duplicate trade in upload batch"))
            continue
        seen_keys.add(dedupe_key)
        trade = Trade(user_id=user_id, strategy_id=strategy.id, source_type=SourceType(source_type).value, instrument=record.instrument, symbol=record.symbol, side=record.side, entry_time=record.entry_time, exit_time=record.exit_time, entry_price=record.numeric_values["entry_price"], exit_price=record.numeric_values["exit_price"], quantity=record.numeric_values["quantity"], fees=record.numeric_values["fees"], slippage=record.numeric_values["slippage"], pnl=record.numeric_values["pnl"], r_multiple=record.numeric_values["r_multiple"], planned_risk=record.numeric_values["planned_risk"], actual_risk=record.numeric_values["actual_risk"], order_type=record.order_type, session_label=record.session_label, setup_tags=record.setup_tags)
        db.add(trade)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            skipped += 1
            errors.append(RowError(record.row_number, "duplicate_trade", None, "duplicate trade already exists"))
            continue
        inserted += 1
        if record.journal_note:
            journal_entries.append(JournalEntry(user_id=user_id, trade_id=trade.id, strategy_id=strategy.id, text=record.journal_note, entry_time=record.entry_time))

    if journal_entries:
        db.add_all(journal_entries)
    db.commit()
    return {"total_rows": total_rows, "inserted": inserted, "skipped": skipped, "errors": [error.__dict__ for error in errors]}
