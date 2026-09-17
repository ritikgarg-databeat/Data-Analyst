"""phase 9b excel exercise test results

Revision ID: 344264c7fc90
Revises: 4e9a8ef2bbb3
Create Date: 2026-09-06 07:26:29.496519

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '344264c7fc90'
down_revision: str | None = '4e9a8ef2bbb3'
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    op.create_table('excel_exercise_test_results',
    sa.Column('attempt_id', sa.String(length=36), nullable=False),
    sa.Column('test_name', sa.String(length=200), nullable=False),
    sa.Column('is_hidden', sa.Boolean(), nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['attempt_id'], ['exercise_attempts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_excel_exercise_test_results_attempt_id'), 'excel_exercise_test_results', ['attempt_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_excel_exercise_test_results_attempt_id'), table_name='excel_exercise_test_results')
    op.drop_table('excel_exercise_test_results')
