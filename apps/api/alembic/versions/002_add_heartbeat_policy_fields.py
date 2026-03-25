"""add status, interval_seconds, last_run_at to heartbeat_policies; change summary to summary_json

Revision ID: 002_add_heartbeat_fields
Revises: 001_add_provider_override
Create Date: 2026-03-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002_add_heartbeat_fields"
down_revision: str | None = "001_add_provider_override"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # HeartbeatPolicy: add status, interval_seconds, last_run_at
    with op.batch_alter_table("heartbeat_policies") as batch_op:
        batch_op.add_column(
            sa.Column("status", sa.String(30), server_default="active", nullable=False)
        )
        batch_op.add_column(
            sa.Column("interval_seconds", sa.Integer, server_default="300", nullable=False)
        )
        batch_op.add_column(sa.Column("last_run_at", sa.DateTime, nullable=True))

    # HeartbeatRun: rename summary (Text) to summary_json (JSON)
    with op.batch_alter_table("heartbeat_runs") as batch_op:
        batch_op.drop_column("summary")
        batch_op.add_column(sa.Column("summary_json", sa.JSON, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("heartbeat_runs") as batch_op:
        batch_op.drop_column("summary_json")
        batch_op.add_column(sa.Column("summary", sa.Text, nullable=True))

    with op.batch_alter_table("heartbeat_policies") as batch_op:
        batch_op.drop_column("last_run_at")
        batch_op.drop_column("interval_seconds")
        batch_op.drop_column("status")
