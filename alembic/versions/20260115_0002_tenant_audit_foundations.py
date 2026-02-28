"""tenant and governance foundations

Revision ID: 20260115_0002
Revises: 20260101_0001
Create Date: 2026-01-15 00:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = "20260115_0002"
down_revision = "20260101_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="default"))
    op.add_column("sources", sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="default"))
    op.add_column("documents", sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="default"))
    op.add_column("batch_runs", sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="default"))

    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"])
    op.create_index("ix_sources_tenant_id", "sources", ["tenant_id"])
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])
    op.create_index("ix_batch_runs_tenant_id", "batch_runs", ["tenant_id"])
    op.create_unique_constraint("uq_projects_tenant_name", "projects", ["tenant_id", "name"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("parent_token_hash", sa.String(length=128), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_tenant_id", "refresh_tokens", ["tenant_id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_background_jobs_tenant_id", "background_jobs", ["tenant_id"])

    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scope", sa.String(length=16), nullable=False, server_default="global"),
        sa.Column("scope_id", sa.String(length=128), nullable=False, server_default="*"),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("scope", "scope_id", "key", name="uq_feature_flags_scope_key"),
    )


def downgrade() -> None:
    op.drop_table("feature_flags")
    op.drop_index("ix_background_jobs_tenant_id", table_name="background_jobs")
    op.drop_table("background_jobs")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_tenant_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_audit_events_tenant_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_constraint("uq_projects_tenant_name", "projects", type_="unique")
    op.drop_index("ix_batch_runs_tenant_id", table_name="batch_runs")
    op.drop_index("ix_documents_tenant_id", table_name="documents")
    op.drop_index("ix_sources_tenant_id", table_name="sources")
    op.drop_index("ix_projects_tenant_id", table_name="projects")

    op.drop_column("batch_runs", "tenant_id")
    op.drop_column("documents", "tenant_id")
    op.drop_column("sources", "tenant_id")
    op.drop_column("projects", "tenant_id")
