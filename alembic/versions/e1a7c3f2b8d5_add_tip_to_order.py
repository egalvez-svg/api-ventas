"""add_tip_to_order

Revision ID: e1a7c3f2b8d5
Revises: 40952b16f974
Create Date: 2026-05-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1a7c3f2b8d5'
down_revision: Union[str, Sequence[str], None] = '40952b16f974'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('order', sa.Column('tip', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('order', 'tip')
