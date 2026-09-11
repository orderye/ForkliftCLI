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
            sa.Column('created_at', sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
        )

    # extend users（batch 模式兼容 SQLite；列已存在则跳过，兼容 create_all 先行的开发库）
    # 注意：status / is_super_admin 已随账户体系拆分废弃——管理员权限来自
    # account-service 的管理员令牌，本地 users 表不再存角色字段。
    new_columns = {
        'enterprise_id': sa.Column(
            'enterprise_id', sa.Integer(),
            sa.ForeignKey('enterprises.id', name='fk_users_enterprise_id'),
            nullable=True,
        ),
        'last_login_at': sa.Column('last_login_at', sa.DateTime(), nullable=True),
    }
    missing = [col for name, col in new_columns.items() if not _has_column('users', name)]
    if missing:
        with op.batch_alter_table('users') as batch_op:
            for col in missing:
                batch_op.add_column(col)

    # 清掉历史遗留的角色列（旧开发库里存在，当前模型与代码都不再使用）
    bind = op.get_bind()
    stale = {'status', 'is_super_admin'}
    for ix in inspect(bind).get_indexes('users'):
        if set(ix['column_names']) & stale:
            op.drop_index(ix['name'], table_name='users')
    with op.batch_alter_table('users') as batch_op:
        for col in sorted(stale):
            if _has_column('users', col):
                batch_op.drop_column(col)

    # admin_audit_logs
    if not _has_table('admin_audit_logs'):
        op.create_table(
            'admin_audit_logs',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column(
                'admin_user_id', sa.Integer(),
                sa.ForeignKey('users.id', name='fk_audit_logs_admin_user'),
                nullable=True,
            ),
            sa.Column('action', sa.String(length=50), nullable=False),
            sa.Column('target_type', sa.String(length=50), nullable=False),
            sa.Column('target_id', sa.Integer(), nullable=True),
            sa.Column('before_json', sa.JSON(), nullable=True),
            sa.Column('after_json', sa.JSON(), nullable=True),
            sa.Column('ip', sa.String(length=45), default=''),
            sa.Column('created_at', sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
        )

    # 历史遗留库里 admin_audit_logs.admin_user_id 曾是 NOT NULL。该列必须可空——
    # account-service 侧的管理员在本地 users 表没有投影，审计日志不能因此写不进去。
    # SQLite 修改空约束需要重建表，batch 模式自动处理。
    audit_cols = inspect(op.get_bind()).get_columns('admin_audit_logs') if _has_table('admin_audit_logs') else []
    if any(c['name'] == 'admin_user_id' and c['nullable'] is False for c in audit_cols):
        with op.batch_alter_table('admin_audit_logs') as batch_op:
            batch_op.alter_column('admin_user_id', nullable=True)


def downgrade() -> None:
    if _has_table('admin_audit_logs'):
        op.drop_table('admin_audit_logs')
    # 与订阅迁移同理：先删落在被删列上的索引，SQLite batch 重建才不会报错
    # 只回退本迁移新增的列；status/is_super_admin 是废弃列，两个方向都不再恢复
    dropped = {'last_login_at', 'enterprise_id'}
    for ix in inspect(op.get_bind()).get_indexes('users'):
        if set(ix['column_names']) & dropped:
            op.drop_index(ix['name'], table_name='users')
    with op.batch_alter_table('users') as batch_op:
        for col in ('last_login_at', 'enterprise_id'):
            if _has_column('users', col):
                batch_op.drop_column(col)
    if _has_table('enterprises'):
        op.drop_table('enterprises')
