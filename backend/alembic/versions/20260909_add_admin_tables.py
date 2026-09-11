"""add admin tables: enterprises, admin_audit_logs; extend users

Revision ID: 20260909_add_admin_tables
Revises: 20260909_add_ai_tables
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '20260909_add_admin_tables'
down_revision = '20260909_add_ai_tables'
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return any(c['name'] == column_name for c in inspect(bind).get_columns(table_name))


def upgrade() -> None:
    # enterprises
    if not _has_table('enterprises'):
        op.create_table(
            'enterprises',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('code', sa.String(length=50), unique=True, nullable=False),
            sa.Column('contact_name', sa.String(length=50), default=''),
            sa.Column('contact_phone', sa.String(length=20), default=''),
            sa.Column('address', sa.String(length=255), default=''),
            sa.Column('plan', sa.String(length=20), default='free'),
            sa.Column('plan_expire_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=20), default='active'),
            sa.Column('created_at', sa.DateTime(), default=sa.func.datetime('now')),
        )

    # extend users（batch 模式兼容 SQLite；列已存在则跳过，兼容 create_all 先行的开发库）
    new_columns = {
        'enterprise_id': sa.Column(
            'enterprise_id', sa.Integer(),
            sa.ForeignKey('enterprises.id', name='fk_users_enterprise_id'),
            nullable=True,
        ),
        'status': sa.Column('status', sa.String(length=20), server_default='active'),
        'last_login_at': sa.Column('last_login_at', sa.DateTime(), nullable=True),
        'is_super_admin': sa.Column('is_super_admin', sa.Boolean(), server_default=sa.text('false')),
    }
    missing = [col for name, col in new_columns.items() if not _has_column('users', name)]
    if missing:
        with op.batch_alter_table('users') as batch_op:
            for col in missing:
                batch_op.add_column(col)

    # admin_audit_logs
    if not _has_table('admin_audit_logs'):
        op.create_table(
            'admin_audit_logs',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column(
                'admin_user_id', sa.Integer(),
                sa.ForeignKey('users.id', name='fk_audit_logs_admin_user'),
                nullable=False,
            ),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('target_type', sa.String(length=50), nullable=False),
            sa.Column('target_id', sa.Integer(), nullable=True),
            sa.Column('before_json', sa.JSON(), nullable=True),
            sa.Column('after_json', sa.JSON(), nullable=True),
            sa.Column('ip', sa.String(length=45), default=''),
            sa.Column('created_at', sa.DateTime(), default=sa.func.datetime('now')),
        )


def downgrade() -> None:
    op.drop_table('admin_audit_logs')
    with op.batch_alter_table('users') as batch_op:
        for col in ('is_super_admin', 'last_login_at', 'status', 'enterprise_id'):
            if _has_column('users', col):
                batch_op.drop_column(col)
    op.drop_table('enterprises')
