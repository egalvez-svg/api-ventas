"""multi-branch user memberships

Revision ID: d5e3f9a0b1c2
Revises: c4f8a2e1b3d9
Create Date: 2026-04-27 20:10:00.000000

Changes:
- Create userbranchrole table
- Migrate existing user.role + user.branch_id → userbranchrole rows
- Add role + branch_id columns to refreshtoken (populated from user before drop)
- Drop role and branch_id columns from user
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "d5e3f9a0b1c2"
down_revision: Union[str, Sequence[str], None] = "c4f8a2e1b3d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create userbranchrole table
    op.create_table(
        "userbranchrole",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branch.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_userbranchrole_user_id", "userbranchrole", ["user_id"])
    op.create_index("ix_userbranchrole_branch_id", "userbranchrole", ["branch_id"])

    # 2. Migrate existing users: copy role+branch_id → userbranchrole
    op.execute(
        """
        INSERT INTO userbranchrole (user_id, branch_id, role, is_active)
        SELECT id, branch_id, role, true
        FROM "user"
        """
    )

    # 3. Add role to refreshtoken (server_default allows it on existing rows,
    #    then we overwrite from user before dropping the user.role column)
    op.add_column(
        "refreshtoken",
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="admin"),
    )
    op.execute(
        """
        UPDATE refreshtoken rt
        SET role = u.role
        FROM "user" u
        WHERE u.id = rt.user_id
        """
    )
    op.alter_column("refreshtoken", "role", server_default=None)

    # 4. Add branch_id to refreshtoken (populated from user.branch_id)
    op.add_column(
        "refreshtoken",
        sa.Column("branch_id", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE refreshtoken rt
        SET branch_id = u.branch_id
        FROM "user" u
        WHERE u.id = rt.user_id
        """
    )
    op.create_foreign_key(
        "fk_refreshtoken_branch_id", "refreshtoken", "branch", ["branch_id"], ["id"]
    )

    # 5. Drop role and branch_id from user
    op.drop_constraint("user_branch_id_fkey", "user", type_="foreignkey")
    op.drop_column("user", "branch_id")
    op.drop_column("user", "role")


def downgrade() -> None:
    # Restore role and branch_id on user (from first membership per user)
    op.add_column("user", sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="waiter"))
    op.add_column("user", sa.Column("branch_id", sa.Integer(), nullable=True))
    op.create_foreign_key("user_branch_id_fkey", "user", "branch", ["branch_id"], ["id"])
    op.execute(
        """
        UPDATE "user" u
        SET role = ubr.role, branch_id = ubr.branch_id
        FROM (
            SELECT DISTINCT ON (user_id) user_id, role, branch_id
            FROM userbranchrole
            ORDER BY user_id, id
        ) ubr
        WHERE ubr.user_id = u.id
        """
    )
    op.alter_column("user", "role", server_default=None)

    # Remove refreshtoken columns
    op.drop_constraint("fk_refreshtoken_branch_id", "refreshtoken", type_="foreignkey")
    op.drop_column("refreshtoken", "branch_id")
    op.drop_column("refreshtoken", "role")

    # Drop userbranchrole
    op.drop_index("ix_userbranchrole_branch_id", "userbranchrole")
    op.drop_index("ix_userbranchrole_user_id", "userbranchrole")
    op.drop_table("userbranchrole")
