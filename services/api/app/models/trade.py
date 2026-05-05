import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.db.base import Base


class Trade(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trades"
    __table_args__ = (
        CheckConstraint("source_type IN ('backtest', 'live', 'paper')", name="ck_trades_source_type"),
        CheckConstraint("side IN ('long', 'short')", name="ck_trades_side"),
        Index("ix_trades_user_strategy_entry_time", "user_id", "strategy_id", "entry_time"),
        UniqueConstraint("user_id", "strategy_id", "symbol", "side", "entry_time", name="uq_trades_dedupe"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("strategies.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    instrument: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), default=Decimal("0"), nullable=True)
    slippage: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    r_multiple: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    planned_risk: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    actual_risk: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    order_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    session_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    setup_tags: Mapped[list[str] | dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    trade_context = relationship("TradeContext", back_populates="trade", uselist=False)
    journal_entries = relationship("JournalEntry", back_populates="trade")
