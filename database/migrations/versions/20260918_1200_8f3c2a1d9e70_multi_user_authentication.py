"""multi-user authentication, sessions, administration, and dataset ownership

Revision ID: 8f3c2a1d9e70
Revises: f3c56b619957
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8f3c2a1d9e70"
down_revision: str | None = "f3c56b619957"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Authentication always compares normalized addresses. The legacy app has
    # one seeded row, so normalize it in place before multi-user signup begins.
    op.execute(sa.text("UPDATE users SET email = lower(trim(email))"))
    op.add_column(
        "users",
        sa.Column(
            "password_hash", sa.String(255), nullable=False, server_default="!unusable"
        ),
    )
    op.add_column(
        "users", sa.Column("role", sa.String(20), nullable=False, server_default="USER")
    )
    op.add_column(
        "users",
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
    )
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "failed_login_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "temporary_password_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_status", "users", ["status"])
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for name, columns in (
        ("user_id", ["user_id"]),
        ("refresh_token_hash", ["refresh_token_hash"]),
        ("expires_at", ["expires_at"]),
    ):
        op.create_index(f"ix_auth_sessions_{name}", "auth_sessions", columns)
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "actor_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "target_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", sa.JSON()),
        sa.Column("request_id", sa.String(64)),
        sa.Column("message", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for name in ("actor_user_id", "target_user_id", "action", "created_at"):
        op.create_index(f"ix_admin_audit_logs_{name}", "admin_audit_logs", [name])
    owner_column = sa.Column("owner_user_id", sa.String(36), nullable=True)
    if op.get_bind().dialect.name == "sqlite":
        # SQLite cannot add a foreign key with ALTER TABLE. Alembic's batch
        # operation recreates and copies this one table transactionally.
        with op.batch_alter_table("datasets") as batch_op:
            batch_op.add_column(owner_column)
            batch_op.create_foreign_key(
                "fk_datasets_owner_user_id_users",
                "users",
                ["owner_user_id"],
                ["id"],
                ondelete="CASCADE",
            )
            batch_op.create_index("ix_datasets_owner_user_id", ["owner_user_id"])
    else:
        op.add_column("datasets", owner_column)
        op.create_foreign_key(
            "fk_datasets_owner_user_id_users",
            "datasets",
            "users",
            ["owner_user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index("ix_datasets_owner_user_id", "datasets", ["owner_user_id"])
    op.add_column(
        "ai_settings",
        sa.Column(
            "admin_access_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "ai_settings",
        sa.Column(
            "admin_daily_request_limit",
            sa.Integer(),
            nullable=False,
            server_default="25",
        ),
    )


def downgrade() -> None:
    op.drop_column("ai_settings", "admin_daily_request_limit")
    op.drop_column("ai_settings", "admin_access_enabled")
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("datasets") as batch_op:
            batch_op.drop_index("ix_datasets_owner_user_id")
            batch_op.drop_constraint(
                "fk_datasets_owner_user_id_users", type_="foreignkey"
            )
            batch_op.drop_column("owner_user_id")
    else:
        op.drop_index("ix_datasets_owner_user_id", table_name="datasets")
        op.drop_constraint(
            "fk_datasets_owner_user_id_users", "datasets", type_="foreignkey"
        )
        op.drop_column("datasets", "owner_user_id")
    op.drop_table("admin_audit_logs")
    op.drop_table("auth_sessions")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    for column in (
        "temporary_password_expires_at",
        "locked_until",
        "failed_login_count",
        "must_change_password",
        "status",
        "role",
        "password_hash",
    ):
        op.drop_column("users", column)
