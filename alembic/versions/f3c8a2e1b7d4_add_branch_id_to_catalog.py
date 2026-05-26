"""add_branch_id_to_catalog

Revision ID: f3c8a2e1b7d4
Revises: e1a7c3f2b8d5
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3c8a2e1b7d4'
down_revision: Union[str, Sequence[str], None] = 'e1a7c3f2b8d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # category: drop global unique index, add branch_id, add composite unique (branch_id, name)
    op.drop_index('ix_category_name', table_name='category')
    op.add_column('category', sa.Column('branch_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key('fk_category_branch_id', 'category', 'branch', ['branch_id'], ['id'])
    op.create_index('ix_category_branch_id', 'category', ['branch_id'])
    op.create_index('uq_category_branch_name', 'category', ['branch_id', 'name'], unique=True)

    # ingredient: add branch_id
    op.add_column('ingredient', sa.Column('branch_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key('fk_ingredient_branch_id', 'ingredient', 'branch', ['branch_id'], ['id'])
    op.create_index('ix_ingredient_branch_id', 'ingredient', ['branch_id'])

    # product: add branch_id
    op.add_column('product', sa.Column('branch_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key('fk_product_branch_id', 'product', 'branch', ['branch_id'], ['id'])
    op.create_index('ix_product_branch_id', 'product', ['branch_id'])


def downgrade() -> None:
    op.drop_index('ix_product_branch_id', table_name='product')
    op.drop_constraint('fk_product_branch_id', 'product', type_='foreignkey')
    op.drop_column('product', 'branch_id')

    op.drop_index('ix_ingredient_branch_id', table_name='ingredient')
    op.drop_constraint('fk_ingredient_branch_id', 'ingredient', type_='foreignkey')
    op.drop_column('ingredient', 'branch_id')

    op.drop_index('uq_category_branch_name', table_name='category')
    op.drop_index('ix_category_branch_id', table_name='category')
    op.drop_constraint('fk_category_branch_id', 'category', type_='foreignkey')
    op.drop_column('category', 'branch_id')
    op.create_index('ix_category_name', 'category', ['name'], unique=True)
