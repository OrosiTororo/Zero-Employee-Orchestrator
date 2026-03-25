"""add provider_override_json to tasks

Revision ID: 001_add_provider_override
Revises: None
Create Date: 2026-03-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001_add_provider_override"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("provider_override_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tasks", "provider_override_json")
