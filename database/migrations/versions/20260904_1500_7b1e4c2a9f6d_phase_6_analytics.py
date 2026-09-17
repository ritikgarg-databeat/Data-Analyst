"""phase 6 statistics/experimentation/business/product analytics

Revision ID: 7b1e4c2a9f6d
Revises: 3a9c7e1f5b2d
Create Date: 2026-09-04 15:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b1e4c2a9f6d'
down_revision: str | None = '3a9c7e1f5b2d'
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    # --- metric_definitions -------------------------------------------------
    # The Metrics Library (spec section 42) — seeded reference data, not
    # user-authored content, so there is no per-user attempt/progress table
    # here (unlike Lesson/Exercise). Statistics/Experimentation/Analytics-Case
    # features added in this phase are otherwise stateless (Statistics/
    # Experiments compute on demand; Analytics Cases are Exercises with a
    # `case-study` tag plus rubric/case-framing fields carried entirely in
    # their content file, matching how prompt/solution already work) — this
    # is the only new table Phase 6 needs.
    op.create_table('metric_definitions',
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('definition', sa.Text(), nullable=False),
    sa.Column('formula', sa.Text(), nullable=True),
    sa.Column('examples', sa.JSON(), nullable=False),
    sa.Column('sql_example', sa.Text(), nullable=True),
    sa.Column('python_example', sa.Text(), nullable=True),
    sa.Column('common_mistakes', sa.JSON(), nullable=False),
    sa.Column('related_metrics', sa.JSON(), nullable=False),
    sa.Column('business_questions', sa.JSON(), nullable=False),
    sa.Column('interview_questions', sa.JSON(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metric_definitions_slug'), 'metric_definitions', ['slug'], unique=True)
    op.create_index(op.f('ix_metric_definitions_category'), 'metric_definitions', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_metric_definitions_category'), table_name='metric_definitions')
    op.drop_index(op.f('ix_metric_definitions_slug'), table_name='metric_definitions')
    op.drop_table('metric_definitions')
