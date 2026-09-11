"""drop unique index on users.email to allow multiple users with blank email

Revision ID: 20260913_002_drop_users_email_unique
Revises: 20260913_merge_all
Create Date: 2026-09-13

"""
from alembic import op
from sqlalchemy import inspect

from app.models import User

revision = '20260913_002_drop_users_email_unique'
down_revision = '20260913_merge_all'
branch_labels = None
depends_on = None

INDEX = 'ix_users_email'


def _indexes():
    return inspect(op.get_bind()).get_indexes('users')


def upgrade() -> None:
    if any(ix['name'] == INDEX for ix in _indexes()):
        op.drop_index(INDEX, table_name='users')


def downgrade() -> None:
    """恢复唯一索引。历史上 email 允许重复（大量空串），直接建唯一索引会失败，
    因此先把空/重复值改成占位值再重建。"""
    if any(ix['name'] == INDEX for ix in _indexes()):
        return

    bind = op.get_bind()
    bind.execute(
        User.__table__.update().where(User.email.is_(None)).values(email='')
    )
    seen = set()
    for row in bind.execute(User.__table__.select()).all():
        value = row['email'] or ''
        if value in seen:
            bind.execute(
                User.__table__.update()
                .where(User.id == row['id'])
                .values(email=f"orphan-{row['id']}@local")
            )
        else:
            seen.add(value)

    op.create_index(INDEX, 'users', ['email'], unique=True)
