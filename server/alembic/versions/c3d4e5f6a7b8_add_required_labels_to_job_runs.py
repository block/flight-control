"""Add required_labels column to job_runs

Revision ID: c3d4e5f6a7b8
Revises: 400553615ce2
Create Date: 2026-02-20 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = '400553615ce2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_runs', sa.Column('required_labels', sa.JSON(), nullable=True, default=dict))


def downgrade() -> None:
    op.drop_column('job_runs', 'required_labels')
