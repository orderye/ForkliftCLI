"""add copyright fields to diagrams, knowledge_documents, model_3d

Revision ID: 20260910_add_copyright_fields
Revises: 20260910_add_subscription
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '20260910_add_copyright_fields'
down_revision = '20260910_merge_heads'
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return any(c['name'] == column_name for c in inspect(bind).get_columns(table_name))


def upgrade() -> None:
    # diagrams
    if _has_table('diagrams'):
        new_cols = {
            'commercial_use': sa.Column('commercial_use', sa.Integer(), server_default='0', nullable=False),
            'copyright_owner': sa.Column('copyright_owner', sa.String(length=200), server_default=''),
            'license_type': sa.Column('license_type', sa.String(length=30), server_default='self_owned', nullable=False),
            'license_expire': sa.Column('license_expire', sa.DateTime(), nullable=True),
        }
        missing = [col for name, col in new_cols.items() if not _has_column('diagrams', name)]
        if missing:
            with op.batch_alter_table('diagrams') as batch_op:
                for col in missing:
                    batch_op.add_column(col)

    # knowledge_documents
    if _has_table('knowledge_documents'):
        new_cols = {
            'commercial_use': sa.Column('commercial_use', sa.Integer(), server_default='0', nullable=False),
            'copyright_owner': sa.Column('copyright_owner', sa.String(length=200), server_default=''),
            'license_type': sa.Column('license_type', sa.String(length=30), server_default='self_owned', nullable=False),
            'license_expire': sa.Column('license_expire', sa.DateTime(), nullable=True),
        }
        missing = [col for name, col in new_cols.items() if not _has_column('knowledge_documents', name)]
        if missing:
            with op.batch_alter_table('knowledge_documents') as batch_op:
                for col in missing:
                    batch_op.add_column(col)

    # model_3d
    if _has_table('model_3d'):
        new_cols = {
            'commercial_use': sa.Column('commercial_use', sa.Integer(), server_default='0', nullable=False),
            'copyright_owner': sa.Column('copyright_owner', sa.String(length=200), server_default=''),
            'license_type': sa.Column('license_type', sa.String(length=30), server_default='self_owned', nullable=False),
            'license_expire': sa.Column('license_expire', sa.DateTime(), nullable=True),
        }
        missing = [col for name, col in new_cols.items() if not _has_column('model_3d', name)]
        if missing:
            with op.batch_alter_table('model_3d') as batch_op:
                for col in missing:
                    batch_op.add_column(col)


def downgrade() -> None:
    with op.batch_alter_table('model_3d') as batch_op:
        for col in ('license_expire', 'license_type', 'copyright_owner', 'commercial_use'):
            if _has_column('model_3d', col):
                batch_op.drop_column(col)

    with op.batch_alter_table('knowledge_documents') as batch_op:
        for col in ('license_expire', 'license_type', 'copyright_owner', 'commercial_use'):
            if _has_column('knowledge_documents', col):
                batch_op.drop_column(col)

    with op.batch_alter_table('diagrams') as batch_op:
        for col in ('license_expire', 'license_type', 'copyright_owner', 'commercial_use'):
            if _has_column('diagrams', col):
                batch_op.drop_column(col)
