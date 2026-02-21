"""Add workspaces, users, and workspace scoping

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create new tables
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )

    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )

    op.create_table(
        'workspace_members',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_member'),
    )
    op.create_index('ix_workspace_members_workspace_id', 'workspace_members', ['workspace_id'])
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'])

    # 2. Seed default workspace, admin user, and membership
    now = sa.func.now()
    op.execute(
        sa.text(
            "INSERT INTO workspaces (id, name, slug, description, created_at, updated_at) "
            "VALUES ('default', 'Default', 'default', 'Default workspace', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO users (id, username, display_name, created_at, updated_at) "
            "VALUES ('admin', 'admin', 'Admin', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO workspace_members (id, workspace_id, user_id, role, created_at, updated_at) "
            "VALUES ('admin-default', 'default', 'admin', 'owner', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )

    # 3. Add user_id to api_keys (nullable)
    with op.batch_alter_table('api_keys') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(), nullable=True))
        batch_op.create_index('ix_api_keys_user_id', ['user_id'])

    # 4. Add workspace_id to existing tables (nullable first, backfill, then NOT NULL)
    tables_needing_workspace = [
        'job_definitions', 'job_runs', 'credentials', 'workers', 'schedules', 'artifacts',
    ]
    for table in tables_needing_workspace:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column('workspace_id', sa.String(), nullable=True, server_default='default'))

    # 5. Backfill workspace_id
    for table in tables_needing_workspace:
        op.execute(sa.text(f"UPDATE {table} SET workspace_id = 'default' WHERE workspace_id IS NULL"))

    # 6. Make workspace_id NOT NULL and add indexes
    for table in tables_needing_workspace:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column('workspace_id', nullable=False)
            batch_op.create_index(f'ix_{table}_workspace_id', ['workspace_id'])

    # 7. Update credential unique constraint: name alone -> (workspace_id, name)
    # Use naming_convention so batch mode can find the auto-named SQLite constraint
    naming_convention = {"uq": "uq_%(table_name)s_%(column_0_name)s"}
    with op.batch_alter_table('credentials', naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint('uq_credentials_name', type_='unique')
        batch_op.create_unique_constraint('uq_credential_workspace_name', ['workspace_id', 'name'])


def downgrade() -> None:
    # Reverse credential constraint
    with op.batch_alter_table('credentials') as batch_op:
        batch_op.drop_constraint('uq_credential_workspace_name', type_='unique')
        batch_op.create_unique_constraint('uq_credentials_name', ['name'])

    # Remove workspace_id from existing tables
    tables = ['job_definitions', 'job_runs', 'credentials', 'workers', 'schedules', 'artifacts']
    for table in tables:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_index(f'ix_{table}_workspace_id')
            batch_op.drop_column('workspace_id')

    # Remove user_id from api_keys
    with op.batch_alter_table('api_keys') as batch_op:
        batch_op.drop_index('ix_api_keys_user_id')
        batch_op.drop_column('user_id')

    # Drop new tables
    op.drop_index('ix_workspace_members_user_id', table_name='workspace_members')
    op.drop_index('ix_workspace_members_workspace_id', table_name='workspace_members')
    op.drop_table('workspace_members')
    op.drop_table('workspaces')
    op.drop_table('users')
