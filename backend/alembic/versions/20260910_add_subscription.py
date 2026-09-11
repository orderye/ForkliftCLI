"""add subscription tables: trial_cards, enterprise_accounts, subscription_logs;
extend users with subscription_level / subscription_expires_at

Revision ID: 20260910_add_subscription
Revises: 20260909_add_admin_tables
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '20260910_add_subscription'
down_revision = '20260909_add_admin_tables'
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return any(c['name'] == column_name for c in inspect(bind).get_columns(table_name))


def upgrade() -> None:
    # trial_cards
    if not _has_table('trial_cards'):
        op.create_table(
            'trial_cards',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('owner_uid', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('target_phone', sa.String(length=20), default=''),
            sa.Column('status', sa.String(length=10), default='unused'),
            sa.Column('expire_at', sa.DateTime(), nullable=True),
            sa.Column('claimed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
        )
        with op.batch_alter_table('trial_cards') as batch_op:
            batch_op.create_index('ix_trial_cards_owner_uid', ['owner_uid'])

    # enterprise_accounts
    if not _has_table('enterprise_accounts'):
        op.create_table(
            'enterprise_accounts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('enterprise_id', sa.Integer(), sa.ForeignKey('enterprises.id'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('enterprise_id', 'user_id', name='uq_enterprise_account'),
        )

    # subscription_logs
    if not _has_table('subscription_logs'):
        op.create_table(
            'subscription_logs',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('action', sa.String(length=20), default=''),
            sa.Column('level_before', sa.String(length=20), default=''),
            sa.Column('level_after', sa.String(length=20), default=''),
            sa.Column('expires_before', sa.DateTime(), nullable=True),
            sa.Column('expires_after', sa.DateTime(), nullable=True),
            sa.Column('note', sa.Text(), default=''),
            sa.Column('created_at', sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
        )

    # extend users
    new_columns = {
        'subscription_level': sa.Column(
            'subscription_level', sa.String(length=20), server_default='free',
        ),
        'subscription_expires_at': sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        'device_token': sa.Column('device_token', sa.String(length=500), server_default=''),
    }
    missing = [col for name, col in new_columns.items() if not _has_column('users', name)]
    if missing:
        with op.batch_alter_table('users') as batch_op:
            for col in missing:
                batch_op.add_column(col)


def downgrade() -> None:
    # SQLite batch 模式重建 users 表时会复制现有索引；落在被删列上的索引必须先删，
    # 否则重建阶段会引用已不存在的列而报错。
    bind = op.get_bind()
    dropped = {'subscription_level', 'subscription_expires_at', 'device_token'}
    for ix in inspect(bind).get_indexes('users'):
        if set(ix['column_names']) & dropped:
            op.drop_index(ix['name'], table_name='users')

    with op.batch_alter_table('users') as batch_op:
        for col in ('device_token', 'subscription_expires_at', 'subscription_level'):
            if _has_column('users', col):
                batch_op.drop_column(col)

    for table in ('subscription_logs', 'enterprise_accounts', 'trial_cards'):
        if _has_table(table):
            op.drop_table(table)
