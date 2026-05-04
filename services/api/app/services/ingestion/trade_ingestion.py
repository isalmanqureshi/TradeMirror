import csv
import io
import json
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import JournalEntry, Strategy, Trade, User

REQUIRED_COLUMNS = {"symbol", "side", "entry_time", "entry_price"}
NUMERIC_FIELDS = {
    "entry_price",
    "exit_price",
    "quantity",
    "pnl",
    "r_multiple",
    "fees",
    "slippage",
    "planned_risk",
    "actual_risk",
}
COLUMN_ALIASES = {
    "entry price": "entry_price",
    "entryprice": "entry_price",
    "p&l": "pnl",
}


@dataclass
class RowError:
    row_number: int
    error: str


def _normalize_column(name: str) -> str:
    key = name.strip().lower()
    key = key.replace(" ", "_")
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
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid datetime for {field}") from exc


def _infer_instrument(symbol: str | None) -> str:
    if not symbol:
        return "unknown"
    return "crypto" if "/" in symbol or symbol.upper().startswith("BTC") else "futures"


def _resolve_user(db: Session, user_id: uuid.UUID | None) -> uuid.UUID:
    if user_id:
        return user_id
    demo_email = "demo@trademirror.local"
    user = db.scalar(select(User).where(User.email == demo_email))
    if user is None:
        user = User(email=demo_email, full_name="Demo User")
        db.add(user)
        db.flush()
    return user.id


def _resolve_strategy(db: Session, user_id: uuid.UUID, strategy_name: str, instrument: str | None) -> Strategy:
    strategy = db.scalar(select(Strategy).where(Strategy.user_id == user_id, Strategy.name == strategy_name))
    if strategy is None:
        strategy = Strategy(user_id=user_id, name=strategy_name, instrument=instrument)
        db.add(strategy)
        db.flush()
    return strategy


def _normalized_rows(file_bytes: bytes) -> tuple[list[str], Iterable[dict[str, str]]]:
    decoded = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    if reader.fieldnames is None:
        raise ValueError("CSV file is missing headers")
    normalized = [_normalize_column(name) for name in reader.fieldnames]
    reader.fieldnames = normalized
    return normalized, reader


def ingest_trade_csv(file: UploadFile, db: Session, user_id: uuid.UUID | None, strategy_name: str, source_type: str) -> dict:
    payload = file.file.read()
    columns, rows = _normalized_rows(payload)

    missing = REQUIRED_COLUMNS - set(columns)
    if missing:
        raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")

    resolved_user_id = _resolve_user(db=db, user_id=user_id)
    inserted = 0
    skipped = 0
    errors: list[RowError] = []
    total_rows = 0

    for row_number, row in enumerate(rows, start=2):
        total_rows += 1
        try:
            symbol = (row.get("symbol") or "").strip()
            side = (row.get("side") or "").strip().lower()
            if not symbol:
                raise ValueError("symbol is required")
            if side not in {"long", "short"}:
                raise ValueError("side must be one of: long, short")

            entry_time = _parse_datetime(row.get("entry_time"), "entry_time")
            if entry_time is None:
                raise ValueError("entry_time is required")

            entry_price = _parse_decimal(row.get("entry_price"), "entry_price")
            if entry_price is None:
                raise ValueError("entry_price is required")

            exit_time = _parse_datetime(row.get("exit_time"), "exit_time")
            if exit_time is not None and exit_time < entry_time:
                raise ValueError("exit_time must be greater than or equal to entry_time")

            instrument = _infer_instrument(symbol)
            strategy = _resolve_strategy(db, resolved_user_id, strategy_name, instrument)

            duplicate = db.scalar(
                select(Trade).where(
                    Trade.user_id == resolved_user_id,
                    Trade.strategy_id == strategy.id,
                    Trade.symbol == symbol,
                    Trade.side == side,
                    Trade.entry_time == entry_time,
                )
            )
            if duplicate is not None:
                skipped += 1
                continue

            numeric_values = {field: _parse_decimal(row.get(field), field) for field in NUMERIC_FIELDS}
            setup_tags = row.get("setup_tags")
            parsed_setup_tags = None
            if setup_tags and setup_tags.strip():
                try:
                    parsed_setup_tags = json.loads(setup_tags)
                except json.JSONDecodeError:
                    parsed_setup_tags = [tag.strip() for tag in setup_tags.split(",") if tag.strip()]

            trade = Trade(
                user_id=resolved_user_id,
                strategy_id=strategy.id,
                source_type=source_type,
                instrument=instrument,
                symbol=symbol,
                side=side,
                entry_time=entry_time,
                exit_time=exit_time,
                entry_price=entry_price,
                exit_price=numeric_values["exit_price"],
                quantity=numeric_values["quantity"],
                fees=numeric_values["fees"],
                slippage=numeric_values["slippage"],
                pnl=numeric_values["pnl"],
                r_multiple=numeric_values["r_multiple"],
                planned_risk=numeric_values["planned_risk"],
                actual_risk=numeric_values["actual_risk"],
                order_type=(row.get("order_type") or None),
                session_label=(row.get("session_label") or None),
                setup_tags=parsed_setup_tags,
            )
            db.add(trade)
            db.flush()

            journal_note = (row.get("journal_note") or "").strip()
            if journal_note:
                db.add(
                    JournalEntry(
                        user_id=resolved_user_id,
                        trade_id=trade.id,
                        strategy_id=strategy.id,
                        text=journal_note,
                        entry_time=entry_time,
                    )
                )

            inserted += 1
        except ValueError as exc:
            errors.append(RowError(row_number=row_number, error=str(exc)))

    db.commit()
    return {
        "total_rows": total_rows,
        "inserted": inserted,
        "skipped": skipped,
        "errors": [error.__dict__ for error in errors],
    }
