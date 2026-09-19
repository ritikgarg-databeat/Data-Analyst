"""recognize the discarded local auth prototype revision

Revision ID: f3c56b619957
Revises: 4d9c395b6197

The local development database was stamped with this revision before that
prototype's code was discarded. Its only column retained by the final design
is ``users.last_login_at``. Keeping this compatibility revision makes the
existing database upgradeable without rewriting its Alembic history, while a
fresh database receives the same retained column before the final auth schema.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3c56b619957"
down_revision: str | None = "4d9c395b6197"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _user_columns() -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}


def upgrade() -> None:
    if "last_login_at" not in _user_columns():
        op.add_column(
            "users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    if "last_login_at" not in _user_columns():
        return
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("last_login_at")
    else:
        op.drop_column("users", "last_login_at")
