"""Add auto-retry columns to job_definitions and job_runs

Revision ID: d4e5f6a7b8c9
Revises: 400553615ce2
Create Date: 2026-02-20 23:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = '400553615ce2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add retry config to job definitions
    op.add_column('job_definitions', sa.Column('max_retries', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('job_definitions', sa.Column('retry_backoff_seconds', sa.Integer(), nullable=False, server_default='60'))
    
    # Add retry tracking to job runs
    op.add_column('job_runs', sa.Column('max_retries', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('job_runs', sa.Column('retry_backoff_seconds', sa.Integer(), nullable=False, server_default='60'))
    op.add_column('job_runs', sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('job_runs', sa.Column('parent_run_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_runs', 'parent_run_id')
    op.drop_column('job_runs', 'attempt_number')
    op.drop_column('job_runs', 'retry_backoff_seconds')
    op.drop_column('job_runs', 'max_retries')
    op.drop_column('job_definitions', 'retry_backoff_seconds')
    op.drop_column('job_definitions', 'max_retries')
