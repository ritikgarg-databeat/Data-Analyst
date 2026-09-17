"""phase_7_data_engineering

Revision ID: 7043d2deffa0
Revises: 7b1e4c2a9f6d
Create Date: 2026-09-05 05:11:08.563003

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7043d2deffa0'
down_revision: str | None = '7b1e4c2a9f6d'
branch_labels: Sequence[str] | str | None = None
depends_on: Sequence[str] | str | None = None


def upgrade() -> None:
    op.create_table('data_models',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('model_kind', sa.Enum('DIMENSIONAL', 'ARCHITECTURE', 'PIPELINE', name='datamodelkind', native_enum=False, length=20), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_models_user_id'), 'data_models', ['user_id'], unique=False)
    op.create_table('data_quality_rules',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('dataset_id', sa.String(length=36), nullable=False),
    sa.Column('table_name', sa.String(length=100), nullable=False),
    sa.Column('column_name', sa.String(length=150), nullable=True),
    sa.Column('rule_type', sa.Enum('NOT_NULL', 'UNIQUE', 'ACCEPTED_VALUES', 'RELATIONSHIP', 'MIN_MAX', 'FRESHNESS', 'ROW_COUNT', name='dataqualityruletype', native_enum=False, length=20), nullable=False),
    sa.Column('config', sa.JSON(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_quality_rules_dataset_id'), 'data_quality_rules', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_data_quality_rules_user_id'), 'data_quality_rules', ['user_id'], unique=False)
    op.create_table('dbt_runs',
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('command', sa.Enum('RUN', 'TEST', 'BUILD', 'COMPILE', 'DOCS_GENERATE', name='dbtcommand', native_enum=False, length=20), nullable=False),
    sa.Column('selector', sa.String(length=200), nullable=True),
    sa.Column('status', sa.Enum('SUCCESS', 'FAILED', 'ERROR', name='dbtrunstatus', native_enum=False, length=10), nullable=False),
    sa.Column('summary', sa.JSON(), nullable=False),
    sa.Column('log', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dbt_runs_user_id'), 'dbt_runs', ['user_id'], unique=False)
    op.create_table('data_model_tables',
    sa.Column('data_model_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('table_type', sa.Enum('FACT', 'DIMENSION', 'BRIDGE', 'SOURCE', 'STORAGE', 'WAREHOUSE', 'TRANSFORM', 'SERVICE', 'STREAM', 'BI', 'OTHER', name='datamodeltabletype', native_enum=False, length=20), nullable=False),
    sa.Column('grain', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('columns', sa.JSON(), nullable=False),
    sa.Column('position_x', sa.Float(), nullable=False),
    sa.Column('position_y', sa.Float(), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['data_model_id'], ['data_models.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_model_tables_data_model_id'), 'data_model_tables', ['data_model_id'], unique=False)
    op.create_table('data_quality_runs',
    sa.Column('rule_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.Enum('PASS', 'FAIL', 'ERROR', name='dataqualitystatus', native_enum=False, length=10), nullable=False),
    sa.Column('expected_value', sa.Text(), nullable=True),
    sa.Column('actual_value', sa.Text(), nullable=True),
    sa.Column('details', sa.JSON(), nullable=False),
    sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.ForeignKeyConstraint(['rule_id'], ['data_quality_rules.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_quality_runs_executed_at'), 'data_quality_runs', ['executed_at'], unique=False)
    op.create_index(op.f('ix_data_quality_runs_rule_id'), 'data_quality_runs', ['rule_id'], unique=False)
    op.create_table('data_model_relationships',
    sa.Column('data_model_id', sa.String(length=36), nullable=False),
    sa.Column('from_table_id', sa.String(length=36), nullable=False),
    sa.Column('to_table_id', sa.String(length=36), nullable=False),
    sa.Column('from_column', sa.String(length=150), nullable=True),
    sa.Column('to_column', sa.String(length=150), nullable=True),
    sa.Column('relationship_type', sa.Enum('ONE_TO_ONE', 'ONE_TO_MANY', 'MANY_TO_ONE', 'MANY_TO_MANY', 'FLOW', 'DEPENDS_ON', name='datamodelrelationshiptype', native_enum=False, length=20), nullable=False),
    sa.Column('label', sa.String(length=200), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['data_model_id'], ['data_models.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['from_table_id'], ['data_model_tables.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['to_table_id'], ['data_model_tables.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_model_relationships_data_model_id'), 'data_model_relationships', ['data_model_id'], unique=False)
    op.create_index(op.f('ix_data_model_relationships_from_table_id'), 'data_model_relationships', ['from_table_id'], unique=False)
    op.create_index(op.f('ix_data_model_relationships_to_table_id'), 'data_model_relationships', ['to_table_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_data_model_relationships_to_table_id'), table_name='data_model_relationships')
    op.drop_index(op.f('ix_data_model_relationships_from_table_id'), table_name='data_model_relationships')
    op.drop_index(op.f('ix_data_model_relationships_data_model_id'), table_name='data_model_relationships')
    op.drop_table('data_model_relationships')
    op.drop_index(op.f('ix_data_quality_runs_rule_id'), table_name='data_quality_runs')
    op.drop_index(op.f('ix_data_quality_runs_executed_at'), table_name='data_quality_runs')
    op.drop_table('data_quality_runs')
    op.drop_index(op.f('ix_data_model_tables_data_model_id'), table_name='data_model_tables')
    op.drop_table('data_model_tables')
    op.drop_index(op.f('ix_dbt_runs_user_id'), table_name='dbt_runs')
    op.drop_table('dbt_runs')
    op.drop_index(op.f('ix_data_quality_rules_user_id'), table_name='data_quality_rules')
    op.drop_index(op.f('ix_data_quality_rules_dataset_id'), table_name='data_quality_rules')
    op.drop_table('data_quality_rules')
    op.drop_index(op.f('ix_data_models_user_id'), table_name='data_models')
    op.drop_table('data_models')
