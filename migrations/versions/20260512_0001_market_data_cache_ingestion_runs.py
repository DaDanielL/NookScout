"""Create market data cache and ingestion run tables.

Revision ID: 20260512_0001
Revises:
Create Date: 2026-05-12 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this migration."""
    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("asset_type", sa.String(length=30), nullable=False),
        sa.Column("primary_exchange", sa.String(length=30), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_otc", sa.Boolean(), nullable=False),
        sa.Column("market_cap", sa.Numeric(24, 4), nullable=True),
        sa.Column("average_daily_volume", sa.BigInteger(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_recency", sa.String(length=30), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "provider", name="uq_tickers_symbol_provider"),
    )
    op.create_index("ix_tickers_symbol_provider", "tickers", ["symbol", "provider"])

    op.create_table(
        "daily_candles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(18, 6), nullable=False),
        sa.Column("high", sa.Numeric(18, 6), nullable=False),
        sa.Column("low", sa.Numeric(18, 6), nullable=False),
        sa.Column("close", sa.Numeric(18, 6), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.Column("vwap", sa.Numeric(18, 6), nullable=True),
        sa.Column("trade_count", sa.BigInteger(), nullable=True),
        sa.Column("adjusted", sa.Boolean(), nullable=False),
        sa.Column("data_recency", sa.String(length=30), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "symbol",
            "provider",
            "session_date",
            "adjusted",
            name="uq_daily_candles_symbol_provider_session_adjusted",
        ),
    )
    op.create_index(
        "ix_daily_candles_symbol_session_date",
        "daily_candles",
        ["symbol", "session_date"],
    )
    op.create_index(
        "ix_daily_candles_symbol_provider_session_date",
        "daily_candles",
        ["symbol", "provider", "session_date"],
    )

    op.create_table(
        "quote_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("last_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("bid_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("ask_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("day_open", sa.Numeric(18, 6), nullable=True),
        sa.Column("day_high", sa.Numeric(18, 6), nullable=True),
        sa.Column("day_low", sa.Numeric(18, 6), nullable=True),
        sa.Column("previous_close", sa.Numeric(18, 6), nullable=False),
        sa.Column("day_volume", sa.BigInteger(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_recency", sa.String(length=30), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "symbol",
            "provider",
            "as_of",
            name="uq_quote_snapshots_symbol_provider_as_of",
        ),
    )
    op.create_index(
        "ix_quote_snapshots_symbol_provider_retrieved_at",
        "quote_snapshots",
        ["symbol", "provider", "retrieved_at"],
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("run_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_symbols", sa.JSON(), nullable=True),
        sa.Column("succeeded_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_runs_provider_run_type_started_at",
        "ingestion_runs",
        ["provider", "run_type", "started_at"],
    )
    op.create_index(
        "ix_ingestion_runs_status_started_at",
        "ingestion_runs",
        ["status", "started_at"],
    )


def downgrade() -> None:
    """Revert this migration."""
    op.drop_index("ix_ingestion_runs_status_started_at", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_provider_run_type_started_at", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")

    op.drop_index("ix_quote_snapshots_symbol_provider_retrieved_at", table_name="quote_snapshots")
    op.drop_table("quote_snapshots")

    op.drop_index("ix_daily_candles_symbol_provider_session_date", table_name="daily_candles")
    op.drop_index("ix_daily_candles_symbol_session_date", table_name="daily_candles")
    op.drop_table("daily_candles")

    op.drop_index("ix_tickers_symbol_provider", table_name="tickers")
    op.drop_table("tickers")
