"""init

Revision ID: ccdbe592ee4e
Revises:
Create Date: 2025-04-16 18:13:48.209486

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ccdbe592ee4e"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("config", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "docker_image",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("image_name", sa.String(), nullable=False),
        sa.Column("config_name", sa.String(), nullable=False),
        sa.Column("config", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("config_name"),
    )
    op.create_table(
        "scenario",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("timestamp_created", sa.DateTime(), nullable=False),
        sa.Column("timestamp_updated", sa.DateTime(), nullable=False),
        sa.Column("steps", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "test_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.Text(), nullable=False),
        sa.Column("db_image", sa.Text(), nullable=False),
        sa.Column("operation", sa.Text(), nullable=False),
        sa.Column("num_records", sa.Integer(), nullable=False),
        sa.Column("step_description", sa.Text(), nullable=True),
        sa.Column("execution_time", sa.Float(), nullable=True),
        sa.Column("memory_used", sa.Float(), nullable=True),
        sa.Column("cpu_percent", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("test_results")
    op.drop_table("scenario")
    op.drop_table("docker_image")
    op.drop_table("ai_config")
