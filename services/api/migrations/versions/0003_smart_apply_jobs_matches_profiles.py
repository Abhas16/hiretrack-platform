"""smart apply jobs matches profiles

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-24 05:53:52.099042+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column(
            "source",
            sa.Enum(
                "GREENHOUSE",
                "LEVER",
                "ASHBY",
                name="job_source",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("company_slug", sa.String(length=100), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("dedupe_hash", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("location", sa.String(length=300), nullable=True),
        sa.Column("is_remote", sa.Boolean(), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("dedupe_hash", name=op.f("uq_jobs_dedupe_hash")),
    )
    op.create_index(
        "ix_jobs_unqueued",
        "jobs",
        ["fetched_at"],
        unique=False,
        postgresql_where=sa.text("queued_at IS NULL"),
    )
    op.create_table(
        "match_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "skills",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "target_roles",
            postgresql.ARRAY(sa.String(length=100)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column(
            "locations",
            postgresql.ARRAY(sa.String(length=100)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("remote_ok", sa.Boolean(), nullable=False),
        sa.Column("years_experience", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_match_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_profiles")),
        sa.UniqueConstraint("user_id", name=op.f("uq_match_profiles_user_id")),
    )
    op.create_table(
        "matches",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column(
            "matched_skills",
            postgresql.ARRAY(sa.String(length=50)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column(
            "gaps",
            postgresql.ARRAY(sa.String(length=200)),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("suggested_resume_variant_id", sa.Uuid(), nullable=True),
        sa.Column("cover_note", sa.Text(), nullable=False),
        sa.Column(
            "resume_bullets",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("kit_provider", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "NEW",
                "APPROVED",
                "SKIPPED",
                name="match_status",
                native_enum=False,
                create_constraint=True,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_matches_application_id_applications"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_matches_job_id_jobs"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["suggested_resume_variant_id"],
            ["resume_variants.id"],
            name=op.f("fk_matches_suggested_resume_variant_id_resume_variants"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_matches_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matches")),
        sa.UniqueConstraint("user_id", "job_id", name="uq_matches_user_id_job_id"),
    )
    op.create_index(op.f("ix_matches_job_id"), "matches", ["job_id"], unique=False)
    op.create_index(
        "ix_matches_user_id_status_score", "matches", ["user_id", "status", "score"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_matches_user_id_status_score", table_name="matches")
    op.drop_index(op.f("ix_matches_job_id"), table_name="matches")
    op.drop_table("matches")
    op.drop_table("match_profiles")
    op.drop_index(
        "ix_jobs_unqueued", table_name="jobs", postgresql_where=sa.text("queued_at IS NULL")
    )
    op.drop_table("jobs")
