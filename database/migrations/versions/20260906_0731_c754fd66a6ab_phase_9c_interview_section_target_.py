"""phase 9c interview section target question count

Revision ID: c754fd66a6ab
Revises: 344264c7fc90
Create Date: 2026-09-06 07:31:54.892691

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c754fd66a6ab'
down_revision: str | None = '344264c7fc90'
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    op.add_column(
        'interview_sections',
        sa.Column('target_question_count', sa.Integer(), nullable=False, server_default='5'),
    )


def downgrade() -> None:
    op.drop_column('interview_sections', 'target_question_count')
