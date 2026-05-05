"""phase 2.1 ingestion hardening constraints

Revision ID: 20260505_01
Revises: 20260502_01
Create Date: 2026-05-05
"""

from alembic import op

revision = "20260505_01"
down_revision = "20260502_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_strategies_user_id_name", "strategies", ["user_id", "name"])
    op.create_unique_constraint("uq_trades_dedupe", "trades", ["user_id", "strategy_id", "symbol", "side", "entry_time"])


def downgrade() -> None:
    op.drop_constraint("uq_trades_dedupe", "trades", type_="unique")
    op.drop_constraint("uq_strategies_user_id_name", "strategies", type_="unique")
