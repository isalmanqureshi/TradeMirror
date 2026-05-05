import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.db.base import Base


class Strategy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "strategies"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_strategies_user_id_name"),
        Index("ix_strategies_user_id_name", "user_id", "name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instrument: Mapped[str | None] = mapped_column(String(50), nullable=True)
    symbol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timeframe: Mapped[str | None] = mapped_column(String(20), nullable=True)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user = relationship("User", back_populates="strategies")
    trades = relationship("Trade", back_populates="strategy")
    journal_entries = relationship("JournalEntry", back_populates="strategy")
    backtest_runs = relationship("BacktestRun", back_populates="strategy")
    analytics_snapshots = relationship("AnalyticsSnapshot", back_populates="strategy")
