"""add user auth fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-27 00:01:00.000000+00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NOT NULL without defaults: assumes the users table has no rows yet
    op.add_column("users", sa.Column("email", sa.String(length=320), nullable=False))
    op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=False))
    op.add_column("users", sa.Column("salt", sa.String(length=64), nullable=False))
    op.create_unique_constraint(op.f("uq_users_email"), "users", ["email"])


def downgrade() -> None:
    op.drop_constraint(op.f("uq_users_email"), "users", type_="unique")
    op.drop_column("users", "salt")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
