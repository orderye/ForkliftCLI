"""create the base schema from ORM models (root revision)

历史链路的起点是一个「增量子迁移」(20240908_add_model3d_version_fields)，它假设
users / model_3d / forklift_models 等表已经存在，因此在空库上执行
`alembic upgrade head` 会立即报 NoSuchTableError，全新安装和 CI 都跑不通。

本修订把 app.models 中描述的完整基础结构落成真实 DDL，作为真正的根迁移；
后续历史增量迁移（版本号字段、AI 表、admin 表、版权字段、订阅/支付…）在其后顺序执行。

幂等：只创建尚不存在的表，已建好结构的开发库执行后为空操作。

Revision ID: 20000101_000_base_schema
Revises:
Create Date: 2026-09-11

"""
from alembic import op
from sqlalchemy import inspect


revision = '20000101_000_base_schema'
down_revision = None
branch_labels = None
depends_on = None


def _metadata():
    """确保所有模型已注册到 Base.metadata 后再取元数据。"""
    from app.core.database import Base
    import app.models  # noqa: F401  导入即注册
    return Base.metadata


def upgrade() -> None:
    metadata = _metadata()
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    pending = [metadata.tables[name] for name in metadata.tables if name not in existing]
    if pending:
        metadata.create_all(bind=bind, tables=pending)


def downgrade() -> None:
    metadata = _metadata()
    bind = op.get_bind()
    for table in reversed(list(metadata.sorted_tables)):
        if table.name in inspect(bind).get_table_names():
            table.drop(bind, checkfirst=True)
