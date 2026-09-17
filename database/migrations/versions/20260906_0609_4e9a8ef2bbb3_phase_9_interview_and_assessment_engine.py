"""phase 9 interview and assessment engine

Revision ID: 4e9a8ef2bbb3
Revises: a6cbbfa6b675
Create Date: 2026-09-06 06:09:44.443521

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e9a8ef2bbb3'
down_revision: str | None = 'a6cbbfa6b675'
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    op.create_table('interview_templates',
    sa.Column('slug', sa.String(length=150), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('target_profile', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('sections', sa.JSON(), nullable=False),
    sa.Column('rubric_weights', sa.JSON(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('content_reference', sa.String(length=500), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_templates_slug'), 'interview_templates', ['slug'], unique=True)
    op.create_table('interview_bookmarks',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('target_type', sa.Enum('QUESTION', 'CASE', 'ASSESSMENT', 'INTERVIEW', 'SKILL', name='interviewtargettype', native_enum=False, length=20), nullable=False),
    sa.Column('target_id', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_bookmarks_target_id'), 'interview_bookmarks', ['target_id'], unique=False)
    op.create_index(op.f('ix_interview_bookmarks_user_id'), 'interview_bookmarks', ['user_id'], unique=False)
    op.create_table('interview_notes',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('target_type', sa.Enum('QUESTION', 'CASE', 'ASSESSMENT', 'INTERVIEW', 'SKILL', name='interviewtargettype', native_enum=False, length=20), nullable=False),
    sa.Column('target_id', sa.String(length=100), nullable=False),
    sa.Column('note', sa.Text(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_notes_target_id'), 'interview_notes', ['target_id'], unique=False)
    op.create_index(op.f('ix_interview_notes_user_id'), 'interview_notes', ['user_id'], unique=False)
    op.create_table('interview_plans',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('days', sa.JSON(), nullable=False),
    sa.Column('readiness_snapshot', sa.JSON(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_plans_user_id'), 'interview_plans', ['user_id'], unique=False)
    op.create_table('interviews',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('template_id', sa.String(length=36), nullable=True),
    sa.Column('mode', sa.Enum('PRACTICE', 'TIMED', 'MOCK', 'COMPANY_STYLE', 'WEAKNESS_DRILL', 'FINAL_READINESS', name='interviewmode', native_enum=False, length=20), nullable=False),
    sa.Column('status', sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'PAUSED', 'COMPLETED', 'ABANDONED', name='interviewstatus', native_enum=False, length=20), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('total_time_limit_seconds', sa.Integer(), nullable=True),
    sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
    sa.Column('current_section_index', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('score', sa.JSON(), nullable=True),
    sa.Column('feedback', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['template_id'], ['interview_templates.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interviews_template_id'), 'interviews', ['template_id'], unique=False)
    op.create_index(op.f('ix_interviews_user_id'), 'interviews', ['user_id'], unique=False)
    op.create_table('readiness_snapshots',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('overall_score', sa.Float(), nullable=False),
    sa.Column('breakdown', sa.JSON(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_readiness_snapshots_user_id'), 'readiness_snapshots', ['user_id'], unique=False)
    op.create_table('interview_sections',
    sa.Column('interview_id', sa.String(length=36), nullable=False),
    sa.Column('interview_type', sa.String(length=30), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('time_limit_seconds', sa.Integer(), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_sections_interview_id'), 'interview_sections', ['interview_id'], unique=False)
    op.create_table('interview_questions',
    sa.Column('slug', sa.String(length=150), nullable=False),
    sa.Column('exercise_id', sa.String(length=36), nullable=False),
    sa.Column('interview_type', sa.Enum('SQL', 'PYTHON', 'EXCEL', 'STATISTICS', 'AB_TESTING', 'PRODUCT_ANALYTICS', 'BUSINESS_ANALYTICS', 'DATA_INTERPRETATION', 'DATA_VISUALIZATION', 'DATA_MODELING', 'DATA_WAREHOUSING', 'DBT', 'DATA_ENGINEERING', 'BEHAVIORAL', name='interviewquestiontype', native_enum=False, length=30), nullable=False),
    sa.Column('time_limit_seconds', sa.Integer(), nullable=True),
    sa.Column('follow_up_question_ids', sa.JSON(), nullable=False),
    sa.Column('company_archetypes', sa.JSON(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('content_reference', sa.String(length=500), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_questions_exercise_id'), 'interview_questions', ['exercise_id'], unique=False)
    op.create_index(op.f('ix_interview_questions_slug'), 'interview_questions', ['slug'], unique=True)
    op.create_table('interview_question_attempts',
    sa.Column('interview_id', sa.String(length=36), nullable=False),
    sa.Column('section_id', sa.String(length=36), nullable=True),
    sa.Column('interview_question_id', sa.String(length=36), nullable=True),
    sa.Column('case_attempt_id', sa.String(length=36), nullable=True),
    sa.Column('exercise_attempt_id', sa.String(length=36), nullable=True),
    sa.Column('parent_attempt_id', sa.String(length=36), nullable=True),
    sa.Column('is_follow_up', sa.Boolean(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['case_attempt_id'], ['case_attempts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['exercise_attempt_id'], ['exercise_attempts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['interview_question_id'], ['interview_questions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['parent_attempt_id'], ['interview_question_attempts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['section_id'], ['interview_sections.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_question_attempts_case_attempt_id'), 'interview_question_attempts', ['case_attempt_id'], unique=False)
    op.create_index(op.f('ix_interview_question_attempts_exercise_attempt_id'), 'interview_question_attempts', ['exercise_attempt_id'], unique=False)
    op.create_index(op.f('ix_interview_question_attempts_interview_id'), 'interview_question_attempts', ['interview_id'], unique=False)
    op.create_index(op.f('ix_interview_question_attempts_interview_question_id'), 'interview_question_attempts', ['interview_question_id'], unique=False)
    op.create_index(op.f('ix_interview_question_attempts_parent_attempt_id'), 'interview_question_attempts', ['parent_attempt_id'], unique=False)
    op.create_index(op.f('ix_interview_question_attempts_section_id'), 'interview_question_attempts', ['section_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_interview_question_attempts_section_id'), table_name='interview_question_attempts')
    op.drop_index(op.f('ix_interview_question_attempts_parent_attempt_id'), table_name='interview_question_attempts')
    op.drop_index(op.f('ix_interview_question_attempts_interview_question_id'), table_name='interview_question_attempts')
    op.drop_index(op.f('ix_interview_question_attempts_interview_id'), table_name='interview_question_attempts')
    op.drop_index(op.f('ix_interview_question_attempts_exercise_attempt_id'), table_name='interview_question_attempts')
    op.drop_index(op.f('ix_interview_question_attempts_case_attempt_id'), table_name='interview_question_attempts')
    op.drop_table('interview_question_attempts')
    op.drop_index(op.f('ix_interview_questions_slug'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_exercise_id'), table_name='interview_questions')
    op.drop_table('interview_questions')
    op.drop_index(op.f('ix_interview_sections_interview_id'), table_name='interview_sections')
    op.drop_table('interview_sections')
    op.drop_index(op.f('ix_readiness_snapshots_user_id'), table_name='readiness_snapshots')
    op.drop_table('readiness_snapshots')
    op.drop_index(op.f('ix_interviews_user_id'), table_name='interviews')
    op.drop_index(op.f('ix_interviews_template_id'), table_name='interviews')
    op.drop_table('interviews')
    op.drop_index(op.f('ix_interview_plans_user_id'), table_name='interview_plans')
    op.drop_table('interview_plans')
    op.drop_index(op.f('ix_interview_notes_user_id'), table_name='interview_notes')
    op.drop_index(op.f('ix_interview_notes_target_id'), table_name='interview_notes')
    op.drop_table('interview_notes')
    op.drop_index(op.f('ix_interview_bookmarks_user_id'), table_name='interview_bookmarks')
    op.drop_index(op.f('ix_interview_bookmarks_target_id'), table_name='interview_bookmarks')
    op.drop_table('interview_bookmarks')
    op.drop_index(op.f('ix_interview_templates_slug'), table_name='interview_templates')
    op.drop_table('interview_templates')
