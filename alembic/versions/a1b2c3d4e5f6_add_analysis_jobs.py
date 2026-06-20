"""add analysis_jobs table and suggestion column

Revision ID: a1b2c3d4e5f6
Revises: 88f311f0a55f
Create Date: 2026-06-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "88f311f0a55f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analysis_details", sa.Column("suggestion", sa.String(), nullable=True))

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("template_key", sa.String(), nullable=True),
        sa.Column("kind", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("total_errors", sa.Integer(), nullable=True),
        sa.Column("result_file_path", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_jobs_id"), "analysis_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_file_id"), "analysis_jobs", ["file_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_user_id"), "analysis_jobs", ["user_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_status"), "analysis_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_jobs_status"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_user_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_file_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_id"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
    op.drop_column("analysis_details", "suggestion")
