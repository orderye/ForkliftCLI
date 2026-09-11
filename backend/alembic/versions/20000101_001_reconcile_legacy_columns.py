"""align legacy tables built by Base.metadata.create_all with the current models

早期开发库是用 `Base.metadata.create_all` 建的（app/main.py startup），迁移链在它之后才
引入，因此那些库里「表在、列不全」。典型例子：users 表缺 is_active，而
security.get_current_user 会读它，一查就是 `no such column: is_active`，整个认证链路直接崩。

本修订做一次通用的列补齐：凡模型里定义、库里缺失的列，按可空方式补上，
不做唯一约束/索引（避免出现重复索引名，也避免历史数据违反新约束）。

在空库上它是空操作（base 迁移已经建好完整结构）。

Revision ID: 20000101_001_reconcile_legacy_columns
Revises: 20000101_000_base_schema
Create Date: 2026-09-11

"""
import copy

from alembic import op
from sqlalchemy import inspect

revision = '20000101_001_reconcile_legacy_columns'
down_revision = '20000101_000_base_schema'
branch_labels = None
depends_on = None


def _metadata():
    from app.core.database import Base
    import app.models  # noqa: F401  导入即注册
    return Base.metadata


def upgrade() -> None:
    metadata = _metadata()
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name in metadata.tables:
        if table_name not in existing_tables:
            continue
        present = {c['name'] for c in inspector.get_columns(table_name)}
        missing = [c for c in metadata.tables[table_name].columns if c.name not in present]
        if not missing:
            continue

        with op.batch_alter_table(table_name) as batch_op:
            for column in missing:
                # 复制后剥掉约束，保证历史数据不会违反新加的 NOT NULL / 唯一约束
                column = copy.copy(column)
                column.nullable = True
                column.index = False
                if column.foreign_keys:
                    column.foreign_keys = frozenset()
                if column.server_default is not None:
                    column.server_default = None
                batch_op.add_column(column)
        print(f"[{revision}] {table_name}: +{[c.name for c in missing]}")


def downgrade() -> None:
    """回退不可精确还原（无法区分「本修订补的列」与「历史遗留列」），保持空操作。"""
