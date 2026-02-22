"""user bot blocked flag

Revision ID: 20260222_0003
Revises: 20260222_0002
Create Date: 2026-02-22 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260222_0003"
down_revision = "20260222_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("bot_blocked", sa.Boolean(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("users", "bot_blocked")
