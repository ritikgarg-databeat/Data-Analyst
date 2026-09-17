"""phase 8 case study and project engine

Revision ID: a6cbbfa6b675
Revises: 7043d2deffa0
Create Date: 2026-09-05 11:08:09.937707

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6cbbfa6b675'
down_revision: str | None = '7043d2deffa0'
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    op.create_table('cases',
    sa.Column('slug', sa.String(length=150), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('category', sa.Enum('BUSINESS_ANALYTICS', 'PRODUCT_ANALYTICS', 'CUSTOMER_ANALYTICS', 'MARKETING_ANALYTICS', 'OPERATIONS', 'EXPERIMENTATION', 'DATA_QUALITY', 'DATA_ARCHITECTURE', name='casecategory', native_enum=False, length=30), nullable=False),
    sa.Column('difficulty', sa.Enum('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT', name='casedifficulty', native_enum=False, length=20), nullable=False),
    sa.Column('estimated_minutes', sa.Integer(), nullable=False),
    sa.Column('company_context', sa.Text(), nullable=True),
    sa.Column('stakeholder_name', sa.String(length=150), nullable=False),
    sa.Column('stakeholder_role', sa.String(length=150), nullable=False),
    sa.Column('problem_statement', sa.Text(), nullable=False),
    sa.Column('business_context', sa.Text(), nullable=True),
    sa.Column('objective', sa.Text(), nullable=False),
    sa.Column('initial_information', sa.Text(), nullable=True),
    sa.Column('constraints', sa.JSON(), nullable=False),
    sa.Column('available_datasets', sa.JSON(), nullable=False),
    sa.Column('expected_deliverables', sa.JSON(), nullable=False),
    sa.Column('learning_objectives', sa.JSON(), nullable=False),
    sa.Column('stages', sa.JSON(), nullable=False),
    sa.Column('required_exercise_slugs', sa.JSON(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('skills', sa.JSON(), nullable=False),
    sa.Column('clarification_guidance', sa.JSON(), nullable=False),
    sa.Column('rubric', sa.JSON(), nullable=False),
    sa.Column('hints', sa.JSON(), nullable=False),
    sa.Column('reference_solution', sa.JSON(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('content_reference', sa.String(length=500), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cases_slug'), 'cases', ['slug'], unique=True)
    op.create_table('project_templates',
    sa.Column('slug', sa.String(length=150), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('category', sa.Enum('BUSINESS_ANALYTICS', 'PRODUCT_ANALYTICS', 'CUSTOMER_ANALYTICS', 'MARKETING_ANALYTICS', 'OPERATIONS', 'EXPERIMENTATION', 'DATA_QUALITY', 'DATA_ARCHITECTURE', name='casecategory', native_enum=False, length=30), nullable=False),
    sa.Column('business_context', sa.Text(), nullable=True),
    sa.Column('objective', sa.Text(), nullable=False),
    sa.Column('requirements', sa.JSON(), nullable=False),
    sa.Column('suggested_datasets', sa.JSON(), nullable=False),
    sa.Column('milestones', sa.JSON(), nullable=False),
    sa.Column('required_skills', sa.JSON(), nullable=False),
    sa.Column('rubric', sa.JSON(), nullable=False),
    sa.Column('learning_objectives', sa.JSON(), nullable=False),
    sa.Column('estimated_hours', sa.Float(), nullable=True),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('content_reference', sa.String(length=500), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_templates_slug'), 'project_templates', ['slug'], unique=True)
    op.create_table('case_attempts',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('case_id', sa.String(length=36), nullable=False),
    sa.Column('case_version_snapshot', sa.Integer(), nullable=False),
    sa.Column('attempt_number', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'PAUSED', 'SUBMITTED', 'UNDER_REVIEW', 'COMPLETED', name='caseattemptstatus', native_enum=False, length=20), nullable=False),
    sa.Column('current_stage', sa.Enum('UNDERSTAND', 'CLARIFY', 'FRAME', 'EXPLORE', 'ANALYZE', 'VALIDATE', 'INSIGHTS', 'RECOMMEND', 'COMMUNICATE', 'SUBMIT', name='casestage', native_enum=False, length=20), nullable=True),
    sa.Column('clarification_questions', sa.Text(), nullable=True),
    sa.Column('problem_framing', sa.JSON(), nullable=True),
    sa.Column('selected_dataset_slugs', sa.JSON(), nullable=False),
    sa.Column('recommendation', sa.JSON(), nullable=True),
    sa.Column('executive_summary', sa.JSON(), nullable=True),
    sa.Column('reflection', sa.JSON(), nullable=True),
    sa.Column('hints_used', sa.Integer(), nullable=False),
    sa.Column('solution_revealed', sa.Boolean(), nullable=False),
    sa.Column('rubric_selections', sa.JSON(), nullable=False),
    sa.Column('score', sa.JSON(), nullable=True),
    sa.Column('feedback', sa.JSON(), nullable=True),
    sa.Column('time_per_stage_seconds', sa.JSON(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_attempts_case_id'), 'case_attempts', ['case_id'], unique=False)
    op.create_index(op.f('ix_case_attempts_user_id'), 'case_attempts', ['user_id'], unique=False)
    op.create_table('findings',
    sa.Column('case_attempt_id', sa.String(length=36), nullable=True),
    sa.Column('project_id', sa.String(length=36), nullable=True),
    sa.Column('observation', sa.Text(), nullable=False),
    sa.Column('evidence_text', sa.Text(), nullable=True),
    sa.Column('impact', sa.Text(), nullable=True),
    sa.Column('confidence', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='findingconfidence', native_enum=False, length=10), nullable=True),
    sa.Column('related_analysis', sa.Text(), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['case_attempt_id'], ['case_attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_findings_case_attempt_id'), 'findings', ['case_attempt_id'], unique=False)
    op.create_index(op.f('ix_findings_project_id'), 'findings', ['project_id'], unique=False)
    op.create_table('hypotheses',
    sa.Column('case_attempt_id', sa.String(length=36), nullable=True),
    sa.Column('project_id', sa.String(length=36), nullable=True),
    sa.Column('statement', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('UNCHECKED', 'INVESTIGATING', 'SUPPORTED', 'REJECTED', 'INCONCLUSIVE', name='hypothesisstatus', native_enum=False, length=20), nullable=False),
    sa.Column('evidence_text', sa.Text(), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['case_attempt_id'], ['case_attempts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hypotheses_case_attempt_id'), 'hypotheses', ['case_attempt_id'], unique=False)
    op.create_index(op.f('ix_hypotheses_project_id'), 'hypotheses', ['project_id'], unique=False)
    op.create_table('project_artifacts',
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('artifact_type', sa.Enum('SQL_QUERY', 'PYTHON_EXECUTION', 'CHART', 'DATA_MODEL', 'DBT_MODEL', 'NOTE', name='projectartifacttype', native_enum=False, length=20), nullable=False),
    sa.Column('ref_id', sa.String(length=200), nullable=True),
    sa.Column('label', sa.String(length=300), nullable=False),
    sa.Column('snapshot', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_artifacts_project_id'), 'project_artifacts', ['project_id'], unique=False)
    op.create_table('project_datasets',
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_datasets_dataset_id'), 'project_datasets', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_project_datasets_project_id'), 'project_datasets', ['project_id'], unique=False)
    op.create_table('project_milestones',
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('is_completed', sa.Boolean(), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_milestones_project_id'), 'project_milestones', ['project_id'], unique=False)
    op.create_table('evidence',
    sa.Column('finding_id', sa.String(length=36), nullable=True),
    sa.Column('hypothesis_id', sa.String(length=36), nullable=True),
    sa.Column('evidence_type', sa.Enum('SQL_QUERY', 'PYTHON_EXECUTION', 'CHART', 'STATISTIC', 'DATASET', 'DATA_MODEL', 'DBT_MODEL', name='evidencetype', native_enum=False, length=20), nullable=False),
    sa.Column('ref_id', sa.String(length=200), nullable=True),
    sa.Column('label', sa.String(length=300), nullable=False),
    sa.Column('snapshot', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['hypothesis_id'], ['hypotheses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_finding_id'), 'evidence', ['finding_id'], unique=False)
    op.create_index(op.f('ix_evidence_hypothesis_id'), 'evidence', ['hypothesis_id'], unique=False)
    op.add_column('projects', sa.Column('template_id', sa.String(length=36), nullable=True))
    op.add_column('projects', sa.Column('data_model_id', sa.String(length=36), nullable=True))
    op.add_column('projects', sa.Column('objective', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('business_context', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('requirements', sa.JSON(), server_default='[]', nullable=False))
    op.add_column('projects', sa.Column('dbt_model_refs', sa.JSON(), server_default='[]', nullable=False))
    op.add_column('projects', sa.Column('documentation', sa.JSON(), server_default='{}', nullable=False))
    op.add_column('projects', sa.Column('presentation', sa.JSON(), server_default='[]', nullable=False))
    op.add_column('projects', sa.Column('rubric_selections', sa.JSON(), server_default='{}', nullable=False))
    op.add_column('projects', sa.Column('score', sa.JSON(), nullable=True))
    op.add_column('projects', sa.Column('reflection', sa.JSON(), nullable=True))
    op.add_column('projects', sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('projects', sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('projects', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f('ix_projects_data_model_id'), 'projects', ['data_model_id'], unique=False)
    op.create_index(op.f('ix_projects_template_id'), 'projects', ['template_id'], unique=False)
    # batch_alter_table: SQLite has no native ALTER-to-add-a-constraint support
    # (only a copy-and-move rebuild) — batch mode handles that automatically
    # here, and is a no-op wrapper (direct ALTER) on Postgres.
    with op.batch_alter_table('projects') as batch_op:
        batch_op.create_foreign_key(
            'fk_projects_template_id', 'project_templates', ['template_id'], ['id'], ondelete='SET NULL'
        )
        batch_op.create_foreign_key(
            'fk_projects_data_model_id', 'data_models', ['data_model_id'], ['id'], ondelete='SET NULL'
        )
    # `Project.status` used to be a free-form string defaulting to "DRAFT"
    # (Phase 5); it's now typed against CaseAttemptStatus, which has no
    # "DRAFT" value — map existing rows onto the closest equivalent.
    op.execute("UPDATE projects SET status = 'NOT_STARTED' WHERE status = 'DRAFT'")


def downgrade() -> None:
    with op.batch_alter_table('projects') as batch_op:
        batch_op.drop_constraint('fk_projects_data_model_id', type_='foreignkey')
        batch_op.drop_constraint('fk_projects_template_id', type_='foreignkey')
    op.drop_index(op.f('ix_projects_template_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_data_model_id'), table_name='projects')
    op.drop_column('projects', 'completed_at')
    op.drop_column('projects', 'submitted_at')
    op.drop_column('projects', 'started_at')
    op.drop_column('projects', 'reflection')
    op.drop_column('projects', 'score')
    op.drop_column('projects', 'rubric_selections')
    op.drop_column('projects', 'presentation')
    op.drop_column('projects', 'documentation')
    op.drop_column('projects', 'dbt_model_refs')
    op.drop_column('projects', 'requirements')
    op.drop_column('projects', 'business_context')
    op.drop_column('projects', 'objective')
    op.drop_column('projects', 'data_model_id')
    op.drop_column('projects', 'template_id')
    op.drop_index(op.f('ix_evidence_hypothesis_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_finding_id'), table_name='evidence')
    op.drop_table('evidence')
    op.drop_index(op.f('ix_project_milestones_project_id'), table_name='project_milestones')
    op.drop_table('project_milestones')
    op.drop_index(op.f('ix_project_datasets_project_id'), table_name='project_datasets')
    op.drop_index(op.f('ix_project_datasets_dataset_id'), table_name='project_datasets')
    op.drop_table('project_datasets')
    op.drop_index(op.f('ix_project_artifacts_project_id'), table_name='project_artifacts')
    op.drop_table('project_artifacts')
    op.drop_index(op.f('ix_hypotheses_project_id'), table_name='hypotheses')
    op.drop_index(op.f('ix_hypotheses_case_attempt_id'), table_name='hypotheses')
    op.drop_table('hypotheses')
    op.drop_index(op.f('ix_findings_project_id'), table_name='findings')
    op.drop_index(op.f('ix_findings_case_attempt_id'), table_name='findings')
    op.drop_table('findings')
    op.drop_index(op.f('ix_case_attempts_user_id'), table_name='case_attempts')
    op.drop_index(op.f('ix_case_attempts_case_id'), table_name='case_attempts')
    op.drop_table('case_attempts')
    op.drop_index(op.f('ix_project_templates_slug'), table_name='project_templates')
    op.drop_table('project_templates')
    op.drop_index(op.f('ix_cases_slug'), table_name='cases')
    op.drop_table('cases')
