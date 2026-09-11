"""add copyright compliance fields (source/owner/license) to content tables

MASTER_PLAN 4.3 版权合规：
- knowledge_documents: +copyright_owner/license_type/license_expire/commercial_use（已有 source）
- diagrams / model_3d: +source 及其余 4 列

Revision ID: 20260909_add_copyright_fields
Revises: 20260909_add_admin_tables
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


revision = '20260909_add_copyright_fields'
down_revision = '20260909_add_admin_tables'
branch_labels = None
depends_on = None


# 表 → 需要补充的列（存在则跳过，幂等）
TARGETS = {
    'knowledge_documents': [
        'copyright_owner', 'license_type', 'license_expire', 'commercial_use',
    ],
    'diagrams': [
        'source', 'copyright_owner', 'license_type', 'license_expire', 'commercial_use',
    ],
    'model_3d': [
        'source', 'copyright_owner', 'license_type', 'license_expire', 'commercial_use',
    ],
}

COLUMNS = {
    'source': sa.Column('source', sa.String(length=500), nullable=True, server_default=''),
    'copyright_owner': sa.Column('copyright_owner', sa.String(length=200), nullable=True, server_default=''),
    'license_type': sa.Column('license_type', sa.String(length=30), nullable=False, server_default='self_owned'),
    'license_expire': sa.Column('license_expire', sa.DateTime(), nullable=True),
    'commercial_use': sa.Column('commercial_use', sa.Integer(), nullable=False, server_default='0'),
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = reflection.Inspector.from_engine(bind)
    tables = inspector.get_table_names()
    for table, columns in TARGETS.items():
        if table not in tables:
            continue
        existing = {c['name'] for c in inspector.get_columns(table)}
        for name in columns:
            if name not in existing:
                op.add_column(table, COLUMNS[name].copy())


def downgrade() -> None:
    bind = op.get_bind()
    inspector = reflection.Inspector.from_engine(bind)
    tables = inspector.get_table_names()
    for table, columns in TARGETS.items():
        if table not in tables:
            continue
        existing = {c['name'] for c in inspector.get_columns(table)}
        for name in columns:
            if name in existing:
                op.drop_column(table, name)
