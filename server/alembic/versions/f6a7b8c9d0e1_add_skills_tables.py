"""Add skills tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-02-21 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'skills',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('license', sa.String(), nullable=True),
        sa.Column('compatibility', sa.String(), nullable=True),
        sa.Column('metadata_kv', sa.JSON(), nullable=True),
        sa.Column('allowed_tools', sa.String(), nullable=True),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('total_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('file_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'name', name='uq_skill_workspace_name'),
    )
    op.create_index('ix_skills_workspace_id', 'skills', ['workspace_id'])

    op.create_table(
        'skill_files',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('skill_id', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('checksum_sha256', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_skill_files_skill_id', 'skill_files', ['skill_id'])


def downgrade() -> None:
    op.drop_index('ix_skill_files_skill_id', table_name='skill_files')
    op.drop_table('skill_files')
    op.drop_index('ix_skills_workspace_id', table_name='skills')
    op.drop_table('skills')
