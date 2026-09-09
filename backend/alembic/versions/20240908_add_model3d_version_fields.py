"""add model3d version fields

Revision ID: 20240908_add_model3d_version_fields
Revises: 
Create Date: 2024-09-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20240908_add_model3d_version_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add version columns to model_3d table
    op.add_column('model_3d', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('model_3d', sa.Column('content_hash', sa.String(64), nullable=True))
    op.add_column('model_3d', sa.Column('storage_provider', sa.String(20), nullable=True))
    op.add_column('model_3d', sa.Column('storage_key', sa.String(255), nullable=True))
    op.add_column('model_3d', sa.Column('mime_type', sa.String(100), nullable=True))
    op.add_column('model_3d', sa.Column('uploaded_at', sa.DateTime(), nullable=True))
    op.add_column('model_3d', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('model_3d', 'uploaded_at')
    op.drop_column('model_3d', 'mime_type')
    op.drop_column('model_3d', 'storage_key')
    op.drop_column('model_3d', 'storage_provider')
    op.drop_column('model_3d', 'content_hash')
    op.drop_column('model_3d', 'version')