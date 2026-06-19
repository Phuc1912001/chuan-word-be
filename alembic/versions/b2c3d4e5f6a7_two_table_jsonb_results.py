"""normalize to 2 tables: drop analysis_details/results, JSONB results on jobs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Bỏ 2 bảng lỗi per-row (kết quả chuyển sang JSONB trên job)
    op.drop_table("analysis_details")
    op.drop_table("analysis_results")

    # 2) uploaded_files: chỉ giữ metadata file
    op.drop_index("ix_uploaded_files_id", table_name="uploaded_files")
    op.drop_column("uploaded_files", "status")
    op.drop_column("uploaded_files", "score")
    op.drop_column("uploaded_files", "total_errors")
    op.add_column("uploaded_files", sa.Column("size_bytes", sa.Integer(), nullable=True))
    op.add_column("uploaded_files", sa.Column("mime_type", sa.String(), nullable=True))
    op.add_column("uploaded_files", sa.Column("expires_at", sa.DateTime(), nullable=True))

    # 3) analysis_jobs: thêm JSONB kết quả + mốc thời gian + siết kind/status
    op.drop_index("ix_analysis_jobs_id", table_name="analysis_jobs")
    op.add_column("analysis_jobs", sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("analysis_jobs", sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("analysis_jobs", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("analysis_jobs", sa.Column("finished_at", sa.DateTime(), nullable=True))
    op.add_column("analysis_jobs", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.alter_column("analysis_jobs", "kind", existing_type=sa.String(), nullable=False, server_default="analyze")
    op.alter_column("analysis_jobs", "status", existing_type=sa.String(), nullable=False, server_default="PENDING")
    op.create_index(
        "ix_analysis_jobs_file_created",
        "analysis_jobs",
        ["file_id", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_analysis_jobs_file_created", table_name="analysis_jobs")
    op.alter_column("analysis_jobs", "status", existing_type=sa.String(), nullable=True, server_default=None)
    op.alter_column("analysis_jobs", "kind", existing_type=sa.String(), nullable=True, server_default=None)
    op.drop_column("analysis_jobs", "expires_at")
    op.drop_column("analysis_jobs", "finished_at")
    op.drop_column("analysis_jobs", "started_at")
    op.drop_column("analysis_jobs", "details")
    op.drop_column("analysis_jobs", "summary")
    op.create_index("ix_analysis_jobs_id", "analysis_jobs", ["id"], unique=False)

    op.add_column("uploaded_files", sa.Column("total_errors", sa.Integer(), nullable=True))
    op.add_column("uploaded_files", sa.Column("score", sa.Float(), nullable=True))
    op.add_column("uploaded_files", sa.Column("status", sa.String(), nullable=True))
    op.drop_column("uploaded_files", "expires_at")
    op.drop_column("uploaded_files", "mime_type")
    op.drop_column("uploaded_files", "size_bytes")
    op.create_index("ix_uploaded_files_id", "uploaded_files", ["id"], unique=False)

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("rule_code", sa.String(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_results_file_id", "analysis_results", ["file_id"])
    op.create_index("ix_analysis_results_id", "analysis_results", ["id"])

    op.create_table(
        "analysis_details",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=True),
        sa.Column("rule_code", sa.String(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("paragraph_index", sa.Integer(), nullable=True),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("suggestion", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_details_file_id", "analysis_details", ["file_id"])
    op.create_index("ix_analysis_details_id", "analysis_details", ["id"])
