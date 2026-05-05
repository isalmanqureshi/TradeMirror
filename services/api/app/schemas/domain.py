import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserRead(ORMBase):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    created_at: datetime
    updated_at: datetime


class StrategyCreate(BaseModel):
    user_id: uuid.UUID
    name: str
    description: str | None = None
    instrument: str | None = None
    symbol: str | None = None
    style: str | None = None
    timeframe: str | None = None
    parameters: dict[str, Any] | None = None


class StrategyRead(ORMBase, StrategyCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SourceType(str, Enum):
    backtest = "backtest"
    live = "live"
    paper = "paper"


class TradeSide(str, Enum):
    long = "long"
    short = "short"


class TradeCreate(BaseModel):
    user_id: uuid.UUID
    strategy_id: uuid.UUID | None = None
    source_type: SourceType
    instrument: str
    symbol: str
    side: TradeSide
    entry_time: datetime
    exit_time: datetime | None = None
    entry_price: Decimal
    exit_price: Decimal | None = None
    quantity: Decimal | None = None
    fees: Decimal | None = None
    slippage: Decimal | None = None
    pnl: Decimal | None = None
    r_multiple: Decimal | None = None
    planned_risk: Decimal | None = None
    actual_risk: Decimal | None = None
    order_type: str | None = None
    session_label: str | None = None
    setup_tags: list[str] | dict[str, Any] | None = None
    notes: str | None = None


class TradeRead(ORMBase, TradeCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TradeContextCreate(BaseModel):
    trade_id: uuid.UUID
    atr_percentile: Decimal | None = None
    realized_vol_percentile: Decimal | None = None
    vix_level: Decimal | None = None
    volume_percentile: Decimal | None = None
    trend_regime: str | None = None
    volatility_regime: str | None = None
    macro_event_nearby: bool | None = None
    macro_event_name: str | None = None
    minutes_to_event: int | None = None
    spread_at_entry: Decimal | None = None
    spread_at_exit: Decimal | None = None
    liquidity_score: Decimal | None = None
    context_payload: dict[str, Any] | None = None


class TradeContextRead(ORMBase, TradeContextCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class JournalEntryCreate(BaseModel):
    user_id: uuid.UUID
    trade_id: uuid.UUID | None = None
    strategy_id: uuid.UUID | None = None
    entry_time: datetime | None = None
    title: str | None = None
    text: str
    emotion_tags: list[str] | dict[str, Any] | None = None
    mistake_tags: list[str] | dict[str, Any] | None = None


class JournalEntryRead(ORMBase, JournalEntryCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class BacktestRunCreate(BaseModel):
    user_id: uuid.UUID
    strategy_id: uuid.UUID
    name: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    parameters: dict[str, Any] | None = None
    summary_stats: dict[str, Any] | None = None


class BacktestRunRead(ORMBase, BacktestRunCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AnalyticsSnapshotCreate(BaseModel):
    user_id: uuid.UUID
    strategy_id: uuid.UUID | None = None
    snapshot_type: str
    payload: dict[str, Any]


class AnalyticsSnapshotRead(ORMBase, AnalyticsSnapshotCreate):
    id: uuid.UUID
    created_at: datetime
