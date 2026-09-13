"""users 表投影化收尾 — 删除本地账户遗留列

20260913_001 是占位迁移（pass），导致 2026-09-13 之前创建的旧库仍带着
password_hash / role 列（NOT NULL），与「账户权威在 account-service、本地
users 仅投影」的模型不符——回填/同步插入会触发 NOT NULL 约束失败。

本迁移按实际列存在与否安全清理（幂等，可对任意旧库重复执行）。
注意：role 的历史值不迁移——权限归 account-service 的 admins 表。

Revision ID: 20260916_001_users_projection
Revises: 20260910_ingest_knowledge_docs
"""
import sqlalchemy as sa
from alembic import op

revision = "20260916_001_users_projection"
down_revision = "20260910_ingest_knowledge_docs"
branch_labels = None
depends_on = None

_DROP = ("password_hash", "role", "is_super_admin")


def _existing_columns(table: str) -> set[str]:
    conn = op.get_bind()
    return {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()}


def upgrade() -> None:
    cols = _existing_columns("users")
    if not cols:
        return  # 全新库由 base_schema 从 ORM 建，天然无遗留列
    with op.batch_alter_table("users") as batch_op:
        for name in _DROP:
            if name in cols:
                batch_op.drop_column(name)


def downgrade() -> None:
    # 仅恢复列结构（nullable，历史真值归 account-service 无法找回），
    # 供 test_downgrade_to_base_then_reupgrade 的降级链路使用。
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_hash", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("role", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("is_super_admin", sa.Boolean(), nullable=True))
