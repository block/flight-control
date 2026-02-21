"""add webhook columns

Revision ID: b2c3d4e5f6a7
Revises: 400553615ce2
Create Date: 2026-02-20 20:46:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = '400553615ce2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add webhook columns to job_definitions
    op.add_column('job_definitions', sa.Column('webhook_url', sa.String(), nullable=True))
    op.add_column('job_definitions', sa.Column('webhook_secret', sa.String(), nullable=True))

    # Add webhook columns to job_runs (snapshotted from job definition)
    op.add_column('job_runs', sa.Column('webhook_url', sa.String(), nullable=True))
    op.add_column('job_runs', sa.Column('webhook_secret', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_runs', 'webhook_secret')
    op.drop_column('job_runs', 'webhook_url')
    op.drop_column('job_definitions', 'webhook_secret')
    op.drop_column('job_definitions', 'webhook_url')
