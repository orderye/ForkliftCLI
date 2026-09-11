"""drop unique index on users.email to allow multiple users with blank email

Revision ID: 20260913_002_drop_users_email_unique
Revises: 20260913_merge_all
Create Date: 2026-09-13
"""
from alembic import op

revision = '20260913_002_drop_users_email_unique'
down_revision = '20260913_merge_all'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.drop_index('ix_users_email', table_name='users')

def downgrade() -> None:
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
