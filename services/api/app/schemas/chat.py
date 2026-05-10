from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.domain import SourceType


class ChatFilters(BaseModel):
    strategy_id: UUID | None = None
    symbol: str | None = None
    instrument: str | None = None
    source_type: SourceType | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = Field(default=10, ge=1, le=100)


class ChatRequest(ChatFilters):
    message: str = Field(min_length=1)


class IntentClassificationRead(BaseModel):
    primary_intent: str
    secondary_intents: list[str]
    confidence: float
    reason: str


class TradeEvidence(BaseModel):
    trade_id: UUID
    strategy_id: UUID | None = None
    symbol: str
    instrument: str | None = None
    source_type: str
    side: str
    entry_time: datetime
    exit_time: datetime | None = None
    pnl: float | None = None
    r_multiple: float | None = None
    session_label: str | None = None
    order_type: str | None = None


class JournalEvidence(BaseModel):
    journal_entry_id: UUID
    trade_id: UUID | None = None
    strategy_id: UUID | None = None
    entry_time: datetime | None = None
    title: str | None = None
    text_excerpt: str
    emotion_tags: list[str] = Field(default_factory=list)
    mistake_tags: list[str] = Field(default_factory=list)


class TradeContextEvidence(BaseModel):
    trade_id: UUID
    symbol: str | None = None
    entry_time: datetime | None = None
    trend_regime: str | None = None
    volatility_regime: str | None = None
    atr_percentile: float | None = None
    realized_vol_percentile: float | None = None
    macro_event_nearby: bool | None = None
    macro_event_name: str | None = None
    minutes_to_event: int | None = None


class ChatEvidence(BaseModel):
    analytics: dict
    trades: list[TradeEvidence]
    journal_entries: list[JournalEvidence]
    trade_context: list[TradeContextEvidence]


class EvidenceCountsMetadata(BaseModel):
    trades: int
    journal_entries: int
    trade_context: int


class DataQualityMetadata(BaseModel):
    has_analytics: bool
    has_trade_evidence: bool
    has_journal_evidence: bool
    has_context_evidence: bool


class ChatMetadata(BaseModel):
    sample_size: int
    evidence_counts: EvidenceCountsMetadata
    data_quality: DataQualityMetadata


class ChatResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    intent: str
    secondary_intents: list[str]
    answer: str
    evidence: ChatEvidence
    filters: ChatFilters
    warnings: list[str]
    suggested_questions: list[str]
    metadata: ChatMetadata | None = None
