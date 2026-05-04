import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.db.base import Base


class JournalEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "journal_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    trade_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("trades.id"), index=True, nullable=True)
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("strategies.id"), index=True, nullable=True)
    entry_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    emotion_tags: Mapped[list[str] | dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    mistake_tags: Mapped[list[str] | dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user = relationship("User", back_populates="journal_entries")
    trade = relationship("Trade", back_populates="journal_entries")
    strategy = relationship("Strategy", back_populates="journal_entries")
