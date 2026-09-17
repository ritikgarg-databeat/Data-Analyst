"""phase 5 dataset hub

Revision ID: 3a9c7e1f5b2d
Revises: 988f6ea7cd4f
Create Date: 2026-09-04 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a9c7e1f5b2d'
down_revision: str | None = '988f6ea7cd4f'
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    # --- Extend `datasets` ---------------------------------------------
    op.add_column('datasets', sa.Column('source_type', sa.Enum('LOCAL', 'KAGGLE', 'GENERATED', 'PUBLIC_API', 'OTHER', name='datasetsourcetype', native_enum=False, length=20), nullable=False, server_default='LOCAL'))
    op.add_column('datasets', sa.Column('business_domain', sa.String(length=100), nullable=True))
    op.add_column('datasets', sa.Column('license', sa.String(length=150), nullable=True))
    op.add_column('datasets', sa.Column('size_bytes', sa.BigInteger(), nullable=True))
    op.add_column('datasets', sa.Column('status', sa.Enum('AVAILABLE', 'IMPORTING', 'PROFILING', 'READY', 'FAILED', 'ARCHIVED', name='datasetstatus', native_enum=False, length=20), nullable=False, server_default='READY'))
    op.add_column('datasets', sa.Column('status_message', sa.Text(), nullable=True))
    op.add_column('datasets', sa.Column('fingerprint', sa.String(length=64), nullable=True))
    op.add_column('datasets', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('datasets', sa.Column('imported_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('datasets', sa.Column('last_profiled_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('datasets', sa.Column('kaggle_ref', sa.String(length=255), nullable=True))
    with op.batch_alter_table('datasets') as batch_op:
        batch_op.alter_column('source_type', server_default=None)
        batch_op.alter_column('status', server_default=None)
        batch_op.alter_column('version', server_default=None)

    # --- dataset_tables ---------------------------------------------------
    op.create_table('dataset_tables',
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=False),
    sa.Column('file_format', sa.String(length=20), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=True),
    sa.Column('column_count', sa.Integer(), nullable=True),
    sa.Column('size_bytes', sa.BigInteger(), nullable=True),
    sa.Column('grain', sa.String(length=255), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_tables_dataset_id'), 'dataset_tables', ['dataset_id'], unique=False)

    # --- dataset_versions ---------------------------------------------------
    op.create_table('dataset_versions',
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('fingerprint', sa.String(length=64), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=True),
    sa.Column('column_count', sa.Integer(), nullable=True),
    sa.Column('size_bytes', sa.BigInteger(), nullable=True),
    sa.Column('change_summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_versions_dataset_id'), 'dataset_versions', ['dataset_id'], unique=False)

    # --- dataset_relationships ---------------------------------------------------
    op.create_table('dataset_relationships',
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('from_table', sa.String(length=100), nullable=False),
    sa.Column('from_column', sa.String(length=150), nullable=False),
    sa.Column('to_table', sa.String(length=100), nullable=False),
    sa.Column('to_column', sa.String(length=150), nullable=False),
    sa.Column('relationship_type', sa.String(length=20), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_relationships_dataset_id'), 'dataset_relationships', ['dataset_id'], unique=False)

    # --- dataset_notes ---------------------------------------------------
    op.create_table('dataset_notes',
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=True),
    sa.Column('column_name', sa.String(length=150), nullable=True),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_notes_dataset_id'), 'dataset_notes', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_dataset_notes_user_id'), 'dataset_notes', ['user_id'], unique=False)

    # --- dataset_tags ---------------------------------------------------
    op.create_table('dataset_tags',
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('tag_id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('dataset_id', 'tag_id')
    )

    # --- dataset_profiles / dataset_column_profiles / dataset_quality_reports --
    op.create_table('dataset_profiles',
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('row_count', sa.Integer(), nullable=False),
    sa.Column('column_count', sa.Integer(), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=True),
    sa.Column('duplicate_row_count', sa.Integer(), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_profiles_dataset_id'), 'dataset_profiles', ['dataset_id'], unique=False)

    op.create_table('dataset_column_profiles',
    sa.Column('profile_id', sa.String(length=36), nullable=False),
    sa.Column('column_name', sa.String(length=150), nullable=False),
    sa.Column('data_type', sa.String(length=20), nullable=False),
    sa.Column('inferred_sql_type', sa.String(length=50), nullable=False),
    sa.Column('null_count', sa.Integer(), nullable=False),
    sa.Column('null_percentage', sa.Float(), nullable=False),
    sa.Column('unique_count', sa.Integer(), nullable=False),
    sa.Column('unique_percentage', sa.Float(), nullable=False),
    sa.Column('min_value', sa.String(length=255), nullable=True),
    sa.Column('max_value', sa.String(length=255), nullable=True),
    sa.Column('mean', sa.Float(), nullable=True),
    sa.Column('median', sa.Float(), nullable=True),
    sa.Column('std_dev', sa.Float(), nullable=True),
    sa.Column('quantiles', sa.JSON(), nullable=True),
    sa.Column('zero_count', sa.Integer(), nullable=True),
    sa.Column('negative_count', sa.Integer(), nullable=True),
    sa.Column('outlier_count', sa.Integer(), nullable=True),
    sa.Column('outlier_method', sa.String(length=20), nullable=True),
    sa.Column('top_values', sa.JSON(), nullable=True),
    sa.Column('sample_values', sa.JSON(), nullable=True),
    sa.Column('min_length', sa.Integer(), nullable=True),
    sa.Column('max_length', sa.Integer(), nullable=True),
    sa.Column('avg_length', sa.Float(), nullable=True),
    sa.Column('extra', sa.JSON(), nullable=True),
    sa.Column('display_order', sa.Integer(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['profile_id'], ['dataset_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_column_profiles_profile_id'), 'dataset_column_profiles', ['profile_id'], unique=False)

    op.create_table('dataset_quality_reports',
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('overall_score', sa.Float(), nullable=False),
    sa.Column('completeness_score', sa.Float(), nullable=False),
    sa.Column('uniqueness_score', sa.Float(), nullable=False),
    sa.Column('validity_score', sa.Float(), nullable=False),
    sa.Column('consistency_score', sa.Float(), nullable=False),
    sa.Column('duplicate_row_count', sa.Integer(), nullable=False),
    sa.Column('issues', sa.JSON(), nullable=False),
    sa.Column('methodology', sa.Text(), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_quality_reports_dataset_id'), 'dataset_quality_reports', ['dataset_id'], unique=False)

    # --- eda_workspaces / eda_findings ---------------------------------------
    op.create_table('eda_workspaces',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=True),
    sa.Column('state', sa.JSON(), nullable=True),
    sa.Column('overview', sa.JSON(), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_eda_workspaces_dataset_id'), 'eda_workspaces', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_eda_workspaces_user_id'), 'eda_workspaces', ['user_id'], unique=False)

    op.create_table('eda_findings',
    sa.Column('workspace_id', sa.String(length=36), nullable=False),
    sa.Column('observation', sa.Text(), nullable=False),
    sa.Column('evidence', sa.Text(), nullable=True),
    sa.Column('business_implication', sa.Text(), nullable=True),
    sa.Column('recommended_action', sa.Text(), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['eda_workspaces.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_eda_findings_workspace_id'), 'eda_findings', ['workspace_id'], unique=False)

    # --- charts ---------------------------------------------------------
    op.create_table('charts',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('workspace_id', sa.String(length=36), nullable=True),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('chart_type', sa.String(length=20), nullable=False),
    sa.Column('config', sa.JSON(), nullable=False),
    sa.Column('insight_observation', sa.Text(), nullable=True),
    sa.Column('insight_why_it_matters', sa.Text(), nullable=True),
    sa.Column('insight_recommended_action', sa.Text(), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['eda_workspaces.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_charts_dataset_id'), 'charts', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_charts_user_id'), 'charts', ['user_id'], unique=False)
    op.create_index(op.f('ix_charts_workspace_id'), 'charts', ['workspace_id'], unique=False)

    # --- projects ---------------------------------------------------------
    op.create_table('projects',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_dataset_id'), 'projects', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_projects_user_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_dataset_id'), table_name='projects')
    op.drop_table('projects')

    op.drop_index(op.f('ix_charts_workspace_id'), table_name='charts')
    op.drop_index(op.f('ix_charts_user_id'), table_name='charts')
    op.drop_index(op.f('ix_charts_dataset_id'), table_name='charts')
    op.drop_table('charts')

    op.drop_index(op.f('ix_eda_findings_workspace_id'), table_name='eda_findings')
    op.drop_table('eda_findings')
    op.drop_index(op.f('ix_eda_workspaces_user_id'), table_name='eda_workspaces')
    op.drop_index(op.f('ix_eda_workspaces_dataset_id'), table_name='eda_workspaces')
    op.drop_table('eda_workspaces')

    op.drop_index(op.f('ix_dataset_quality_reports_dataset_id'), table_name='dataset_quality_reports')
    op.drop_table('dataset_quality_reports')
    op.drop_index(op.f('ix_dataset_column_profiles_profile_id'), table_name='dataset_column_profiles')
    op.drop_table('dataset_column_profiles')
    op.drop_index(op.f('ix_dataset_profiles_dataset_id'), table_name='dataset_profiles')
    op.drop_table('dataset_profiles')

    op.drop_table('dataset_tags')

    op.drop_index(op.f('ix_dataset_notes_user_id'), table_name='dataset_notes')
    op.drop_index(op.f('ix_dataset_notes_dataset_id'), table_name='dataset_notes')
    op.drop_table('dataset_notes')

    op.drop_index(op.f('ix_dataset_relationships_dataset_id'), table_name='dataset_relationships')
    op.drop_table('dataset_relationships')

    op.drop_index(op.f('ix_dataset_versions_dataset_id'), table_name='dataset_versions')
    op.drop_table('dataset_versions')

    op.drop_index(op.f('ix_dataset_tables_dataset_id'), table_name='dataset_tables')
    op.drop_table('dataset_tables')

    op.drop_column('datasets', 'kaggle_ref')
    op.drop_column('datasets', 'last_profiled_at')
    op.drop_column('datasets', 'imported_at')
    op.drop_column('datasets', 'version')
    op.drop_column('datasets', 'fingerprint')
    op.drop_column('datasets', 'status_message')
    op.drop_column('datasets', 'status')
    op.drop_column('datasets', 'size_bytes')
    op.drop_column('datasets', 'license')
    op.drop_column('datasets', 'business_domain')
    op.drop_column('datasets', 'source_type')
