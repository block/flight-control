"""add auto-retry columns

Revision ID: a1b2c3d4e5f6
Revises: 400553615ce2
Create Date: 2026-02-20 20:35:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '400553615ce2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add retry configuration to job_definitions
    op.add_column('job_definitions', sa.Column('max_retries', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('job_definitions', sa.Column('retry_backoff_seconds', sa.Integer(), nullable=False, server_default='60'))

    # Add retry tracking to job_runs
    op.add_column('job_runs', sa.Column('max_retries', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('job_runs', sa.Column('retry_backoff_seconds', sa.Integer(), nullable=False, server_default='60'))
    op.add_column('job_runs', sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('job_runs', sa.Column('parent_run_id', sa.String(), nullable=True))
    op.add_column('job_runs', sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True))

    # Create index for efficient retry lookups
    op.create_index('ix_job_runs_parent_run_id', 'job_runs', ['parent_run_id'], unique=False)
    op.create_index('ix_job_runs_scheduled_at', 'job_runs', ['scheduled_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_job_runs_scheduled_at', table_name='job_runs')
    op.drop_index('ix_job_runs_parent_run_id', table_name='job_runs')

    op.drop_column('job_runs', 'scheduled_at')
    op.drop_column('job_runs', 'parent_run_id')
    op.drop_column('job_runs', 'attempt_number')
    op.drop_column('job_runs', 'retry_backoff_seconds')
    op.drop_column('job_runs', 'max_retries')

    op.drop_column('job_definitions', 'retry_backoff_seconds')
    op.drop_column('job_definitions', 'max_retries')
