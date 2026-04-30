"""plan-first proposals + transient autonomy overrides

Adds the columns and table introduced in v0.1.8:

* ``plans.goal`` — natural-language goal for standalone proposals
* ``plans.parent_plan_id`` — sub-plan tree for delegated work
* ``plans.delegation_metadata`` — adapter-supplied provenance
* ``plans.ticket_id`` / ``plans.spec_id`` relaxed to NULL so a plan can be
  generated as a pure proposal before a ticket exists
* ``autonomy_session_overrides`` — per-user transient override of the
  company-level AUTONOMY_LEVEL config

Revision ID: 004_plan_proposals_autonomy_overrides
Revises: 003_add_setup_completed
Create Date: 2026-04-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_plan_proposals_autonomy_overrides"
down_revision: str | None = "003_add_setup_completed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("plans") as batch_op:
        batch_op.add_column(sa.Column("goal", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "parent_plan_id",
                sa.Uuid(),
                sa.ForeignKey("plans.id"),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("delegation_metadata", sa.JSON(), nullable=True))
        batch_op.alter_column("ticket_id", existing_type=sa.Uuid(), nullable=True)
        batch_op.alter_column("spec_id", existing_type=sa.Uuid(), nullable=True)
        batch_op.create_index("ix_plans_parent_plan_id", ["parent_plan_id"])

    op.create_table(
        "autonomy_session_overrides",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            sa.Uuid(),
            sa.ForeignKey("companies.id"),
            nullable=True,
        ),
        sa.Column("autonomy_level", sa.String(30), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_autonomy_overrides_user_id",
        "autonomy_session_overrides",
        ["user_id"],
    )
    op.create_index(
        "ix_autonomy_overrides_expires_at",
        "autonomy_session_overrides",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_autonomy_overrides_expires_at", "autonomy_session_overrides")
    op.drop_index("ix_autonomy_overrides_user_id", "autonomy_session_overrides")
    op.drop_table("autonomy_session_overrides")

    with op.batch_alter_table("plans") as batch_op:
        batch_op.drop_index("ix_plans_parent_plan_id")
        batch_op.alter_column("spec_id", existing_type=sa.Uuid(), nullable=False)
        batch_op.alter_column("ticket_id", existing_type=sa.Uuid(), nullable=False)
        batch_op.drop_column("delegation_metadata")
        batch_op.drop_column("parent_plan_id")
        batch_op.drop_column("goal")
