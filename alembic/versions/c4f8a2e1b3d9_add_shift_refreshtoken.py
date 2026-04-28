"""add shift and refreshtoken tables

Revision ID: c4f8a2e1b3d9
Revises: b9e2f1c3d7a8
Create Date: 2026-04-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "c4f8a2e1b3d9"
down_revision: Union[str, Sequence[str], None] = "b9e2f1c3d7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shift",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("opened_by", sa.Integer(), nullable=False),
        sa.Column("closed_by", sa.Integer(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["opened_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["closed_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shift_branch_id", "shift", ["branch_id"])

    op.create_table(
        "refreshtoken",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("shift_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["shift_id"], ["shift.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refreshtoken_token_hash", "refreshtoken", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_refreshtoken_token_hash", "refreshtoken")
    op.drop_table("refreshtoken")
    op.drop_index("ix_shift_branch_id", "shift")
    op.drop_table("shift")
