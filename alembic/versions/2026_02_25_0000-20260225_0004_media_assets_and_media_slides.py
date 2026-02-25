"""media assets and media slides

Revision ID: 20260225_0004
Revises: 20260222_0003
Create Date: 2026-02-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260225_0004"
down_revision = "20260222_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TYPE slidetype ADD VALUE 'MEDIA';
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        "media_assets",
        sa.Column("file_id", sa.String(length=512), nullable=False),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(length=512), nullable=True),
        sa.Column("file_extension", sa.String(length=32), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("file_unique_id", sa.String(length=512), nullable=True),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("file_id"),
    )

    op.add_column("slides", sa.Column("media_asset_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_slides_media_asset_id",
        "slides",
        "media_assets",
        ["media_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_slides_media_asset_id", "slides", type_="foreignkey")
    op.drop_column("slides", "media_asset_id")
    op.drop_table("media_assets")
    # Note: Postgres ENUM values cannot be removed safely in-place.
