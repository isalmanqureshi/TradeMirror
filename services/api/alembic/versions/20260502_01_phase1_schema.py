"""phase 1 schema foundation

Revision ID: 20260502_01
Revises: 
Create Date: 2026-05-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260502_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "strategies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instrument", sa.String(length=50), nullable=True),
        sa.Column("symbol", sa.String(length=50), nullable=True),
        sa.Column("style", sa.String(length=50), nullable=True),
        sa.Column("timeframe", sa.String(length=20), nullable=True),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_strategies_user_id", "strategies", ["user_id"])
    op.create_index("ix_strategies_user_id_name", "strategies", ["user_id", "name"])

    op.create_table(
        "trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("strategies.id"), nullable=True),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("instrument", sa.String(length=50), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("entry_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("exit_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("exit_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=True),
        sa.Column("fees", sa.Numeric(18, 6), nullable=True, server_default="0"),
        sa.Column("slippage", sa.Numeric(18, 6), nullable=True),
        sa.Column("pnl", sa.Numeric(18, 6), nullable=True),
        sa.Column("r_multiple", sa.Numeric(18, 6), nullable=True),
        sa.Column("planned_risk", sa.Numeric(18, 6), nullable=True),
        sa.Column("actual_risk", sa.Numeric(18, 6), nullable=True),
        sa.Column("order_type", sa.String(length=30), nullable=True),
        sa.Column("session_label", sa.String(length=50), nullable=True),
        sa.Column("setup_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source_type IN ('backtest', 'live', 'paper')", name="ck_trades_source_type"),
        sa.CheckConstraint("side IN ('long', 'short')", name="ck_trades_side"),
    )
    op.create_index("ix_trades_user_id", "trades", ["user_id"])
    op.create_index("ix_trades_strategy_id", "trades", ["strategy_id"])
    op.create_index("ix_trades_entry_time", "trades", ["entry_time"])
    op.create_index("ix_trades_symbol", "trades", ["symbol"])
    op.create_index("ix_trades_instrument", "trades", ["instrument"])
    op.create_index("ix_trades_source_type", "trades", ["source_type"])
    op.create_index("ix_trades_user_strategy_entry_time", "trades", ["user_id", "strategy_id", "entry_time"])

    op.create_table("trade_context", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False), sa.Column("trade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trades.id"), nullable=False), sa.Column("atr_percentile", sa.Numeric(10, 4), nullable=True), sa.Column("realized_vol_percentile", sa.Numeric(10, 4), nullable=True), sa.Column("vix_level", sa.Numeric(10, 4), nullable=True), sa.Column("volume_percentile", sa.Numeric(10, 4), nullable=True), sa.Column("trend_regime", sa.String(length=50), nullable=True), sa.Column("volatility_regime", sa.String(length=20), nullable=True), sa.Column("macro_event_nearby", sa.Boolean(), nullable=True), sa.Column("macro_event_name", sa.String(length=255), nullable=True), sa.Column("minutes_to_event", sa.Integer(), nullable=True), sa.Column("spread_at_entry", sa.Numeric(10, 4), nullable=True), sa.Column("spread_at_exit", sa.Numeric(10, 4), nullable=True), sa.Column("liquidity_score", sa.Numeric(10, 4), nullable=True), sa.Column("context_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_trade_context_trade_id", "trade_context", ["trade_id"], unique=True)

    op.create_table("journal_entries", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("trade_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trades.id"), nullable=True), sa.Column("strategy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("strategies.id"), nullable=True), sa.Column("entry_time", sa.DateTime(timezone=True), nullable=True), sa.Column("title", sa.String(length=255), nullable=True), sa.Column("text", sa.Text(), nullable=False), sa.Column("emotion_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column("mistake_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_journal_entries_user_id", "journal_entries", ["user_id"])
    op.create_index("ix_journal_entries_trade_id", "journal_entries", ["trade_id"])
    op.create_index("ix_journal_entries_strategy_id", "journal_entries", ["strategy_id"])

    op.create_table("backtest_runs", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("strategy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("strategies.id"), nullable=False), sa.Column("name", sa.String(length=255), nullable=False), sa.Column("start_date", sa.DateTime(timezone=True)), sa.Column("end_date", sa.DateTime(timezone=True)), sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text())), sa.Column("summary_stats", postgresql.JSONB(astext_type=sa.Text())), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_backtest_runs_user_id", "backtest_runs", ["user_id"])
    op.create_index("ix_backtest_runs_strategy_id", "backtest_runs", ["strategy_id"])

    op.create_table("analytics_snapshots", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False), sa.Column("strategy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("strategies.id"), nullable=True), sa.Column("snapshot_type", sa.String(length=50), nullable=False), sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_analytics_snapshots_user_id", "analytics_snapshots", ["user_id"])
    op.create_index("ix_analytics_snapshots_strategy_id", "analytics_snapshots", ["strategy_id"])
    op.create_index("ix_analytics_snapshots_snapshot_type", "analytics_snapshots", ["snapshot_type"])


def downgrade() -> None:
    op.drop_table("analytics_snapshots")
    op.drop_table("backtest_runs")
    op.drop_table("journal_entries")
    op.drop_table("trade_context")
    op.drop_table("trades")
    op.drop_table("strategies")
    op.drop_table("users")
