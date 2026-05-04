import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.db.base import Base


class TradeContext(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trade_context"

    trade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trades.id"), unique=True, index=True, nullable=False)
    atr_percentile: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    realized_vol_percentile: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    vix_level: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    volume_percentile: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    trend_regime: Mapped[str | None] = mapped_column(String(50), nullable=True)
    volatility_regime: Mapped[str | None] = mapped_column(String(20), nullable=True)
    macro_event_nearby: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    macro_event_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    minutes_to_event: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spread_at_entry: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    spread_at_exit: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    liquidity_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    context_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    trade = relationship("Trade", back_populates="trade_context")
