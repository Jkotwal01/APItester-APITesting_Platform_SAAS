"""Add started_at, completed_at to test_runs; add status, response_time_ms to test_results

Revision ID: a3c9e1f52b08
Revises: 2f46f9030cc0
Create Date: 2026-06-15 12:25:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3c9e1f52b08"
down_revision: str | Sequence[str] | None = "2f46f9030cc0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing columns introduced after the initial schema."""
    # test_runs: add started_at and completed_at
    op.add_column(
        "test_runs",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "test_runs",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # test_results: add status and response_time_ms
    op.add_column(
        "test_results",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="passed"),
    )
    op.add_column(
        "test_results",
        sa.Column("response_time_ms", sa.Float(), nullable=False, server_default="0.0"),
    )


def downgrade() -> None:
    """Remove the added columns."""
    op.drop_column("test_results", "response_time_ms")
    op.drop_column("test_results", "status")
    op.drop_column("test_runs", "completed_at")
    op.drop_column("test_runs", "started_at")
