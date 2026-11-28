"""add shared login throttle and token revocation storage

Revision ID: 9ac41f2b7d31
Revises: fdf898f0509a
Create Date: 2026-11-28
"""
from alembic import op
import sqlalchemy as sa


revision = "9ac41f2b7d31"
down_revision = "fdf898f0509a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_key", sa.String(length=64), nullable=False),
        sa.Column("source_key", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_login_attempts_account_key", "login_attempts", ["account_key"])
    op.create_index("ix_login_attempts_source_key", "login_attempts", ["source_key"])
    op.create_index("ix_login_attempts_created_at", "login_attempts", ["created_at"])
    op.create_index("ix_login_attempt_account_created", "login_attempts", ["account_key", "created_at"])
    op.create_index("ix_login_attempt_source_created", "login_attempts", ["source_key", "created_at"])

    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index("ix_revoked_tokens_user_id", "revoked_tokens", ["user_id"])
    op.create_index("ix_revoked_tokens_expires_at", "revoked_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_revoked_tokens_expires_at", table_name="revoked_tokens")
    op.drop_index("ix_revoked_tokens_user_id", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
    op.drop_index("ix_login_attempt_source_created", table_name="login_attempts")
    op.drop_index("ix_login_attempt_account_created", table_name="login_attempts")
    op.drop_index("ix_login_attempts_created_at", table_name="login_attempts")
    op.drop_index("ix_login_attempts_source_key", table_name="login_attempts")
    op.drop_index("ix_login_attempts_account_key", table_name="login_attempts")
    op.drop_table("login_attempts")
