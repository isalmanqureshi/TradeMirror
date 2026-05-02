import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.db.base import Base


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    strategies = relationship("Strategy", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    journal_entries = relationship("JournalEntry", back_populates="user")
    backtest_runs = relationship("BacktestRun", back_populates="user")
    analytics_snapshots = relationship("AnalyticsSnapshot", back_populates="user")
