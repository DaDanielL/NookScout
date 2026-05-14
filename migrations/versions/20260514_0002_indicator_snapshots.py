"""Create indicator snapshot table.

Revision ID: 20260514_0002
Revises: 20260512_0001
Create Date: 2026-05-14 00:02:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260514_0002"
down_revision: str | None = "20260512_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this migration."""
    op.create_table(
        "indicator_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("calculation_date", sa.Date(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("calculation_version", sa.String(length=80), nullable=False),
        sa.Column("adjusted", sa.Boolean(), nullable=False),
        sa.Column("data_recency", sa.String(length=30), nullable=False),
        sa.Column("input_start_session_date", sa.Date(), nullable=True),
        sa.Column("input_end_session_date", sa.Date(), nullable=True),
        sa.Column("available_candles", sa.Integer(), nullable=False),
        sa.Column("required_candles", sa.Integer(), nullable=False),
        sa.Column("is_complete", sa.Boolean(), nullable=False),
        sa.Column("technical_is_complete", sa.Boolean(), nullable=False),
        sa.Column("support_resistance_is_complete", sa.Boolean(), nullable=False),
        sa.Column("relative_strength_is_complete", sa.Boolean(), nullable=False),
        sa.Column("benchmark_symbols", sa.JSON(), nullable=True),
        sa.Column("relative_strength_lookback_periods", sa.JSON(), nullable=True),
        sa.Column("technical_snapshot", sa.JSON(), nullable=False),
        sa.Column("support_resistance_snapshot", sa.JSON(), nullable=False),
        sa.Column("relative_strength_snapshot", sa.JSON(), nullable=False),
        sa.Column("incomplete_details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_indicator_snapshots_symbol_provider_calculation_date",
        "indicator_snapshots",
        ["symbol", "provider", "calculation_date"],
    )
    op.create_index(
        "ix_indicator_snapshots_symbol_provider_version_date",
        "indicator_snapshots",
        ["symbol", "provider", "calculation_version", "calculation_date"],
    )
    op.create_index(
        "ix_indicator_snapshots_version_calculated_at",
        "indicator_snapshots",
        ["calculation_version", "calculated_at"],
    )


def downgrade() -> None:
    """Revert this migration."""
    op.drop_index(
        "ix_indicator_snapshots_version_calculated_at",
        table_name="indicator_snapshots",
    )
    op.drop_index(
        "ix_indicator_snapshots_symbol_provider_version_date",
        table_name="indicator_snapshots",
    )
    op.drop_index(
        "ix_indicator_snapshots_symbol_provider_calculation_date",
        table_name="indicator_snapshots",
    )
    op.drop_table("indicator_snapshots")
