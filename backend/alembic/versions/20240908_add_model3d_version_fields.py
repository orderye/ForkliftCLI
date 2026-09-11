"""add model3d version fields

Revision ID: 20240908_add_model3d_version_fields
Revises: 20000101_001_reconcile_legacy_columns
Create Date: 2024-09-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20240908_add_model3d_version_fields'
down_revision = '20000101_001_reconcile_legacy_columns'
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using reflection inspector."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)


def upgrade() -> None:
    # Add version columns to model_3d table (idempotent)
    if not _has_column('model_3d', 'version'):
        op.add_column('model_3d', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    if not _has_column('model_3d', 'content_hash'):
        op.add_column('model_3d', sa.Column('content_hash', sa.String(64), nullable=True))
    if not _has_column('model_3d', 'storage_provider'):
        op.add_column('model_3d', sa.Column('storage_provider', sa.String(20), nullable=True))
    if not _has_column('model_3d', 'storage_key'):
        op.add_column('model_3d', sa.Column('storage_key', sa.String(255), nullable=True))
    if not _has_column('model_3d', 'mime_type'):
        op.add_column('model_3d', sa.Column('mime_type', sa.String(100), nullable=True))
    if not _has_column('model_3d', 'uploaded_at'):
        op.add_column('model_3d', sa.Column('uploaded_at', sa.DateTime(), nullable=True))
    if not _has_column('model_3d', 'updated_at'):
        op.add_column('model_3d', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    for col in ('uploaded_at', 'mime_type', 'storage_key', 'storage_provider', 'content_hash', 'version'):
        if _has_column('model_3d', col):
            op.drop_column('model_3d', col)