"""add orderitemextra table

Revision ID: b9e2f1c3d7a8
Revises: 3377e41a9334
Create Date: 2026-04-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "b9e2f1c3d7a8"
down_revision: Union[str, Sequence[str], None] = "3377e41a9334"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orderitemextra",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_item_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredient.id"]),
        sa.ForeignKeyConstraint(["order_item_id"], ["orderitem.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("orderitemextra")
