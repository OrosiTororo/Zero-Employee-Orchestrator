"""add setup_completed to companies

Revision ID: 003_add_setup_completed
Revises: 002_add_heartbeat_fields
Create Date: 2026-03-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "003_add_setup_completed"
down_revision: str | None = "002_add_heartbeat_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("companies") as batch_op:
        batch_op.add_column(
            sa.Column("setup_completed", sa.Boolean, server_default="0", nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table("companies") as batch_op:
        batch_op.drop_column("setup_completed")
