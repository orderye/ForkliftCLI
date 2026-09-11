"""迁移链一致性回归测试

覆盖历史上真实踩过的坑：
1. 空库 `alembic upgrade head` 直接失败（历史链根是一个增量子迁移）
2. 多头（two heads）导致 upgrade head 报 Multiple head revisions
3. 模型与迁移漂移（模型有列、迁移没加，或反过来）
4. 数据播种迁移用 app 全局 engine，读写了错误的库
5. SQLite 专属默认值 datetime('now') 在 PostgreSQL 部署时炸
6. 迁移链回退再升级不一致
"""
import re

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic import command
from sqlalchemy import create_engine, inspect

from conftest import ROOT


def _alembic_config(db_path, script_location=None):
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(script_location or (ROOT / "alembic")))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


@pytest.fixture()
def empty_db(tmp_path):
    return tmp_path / "db.sqlite3"


def test_single_head():
    cfg = _alembic_config("/tmp/__never_used__.db")
    heads = ScriptDirectory.from_config(cfg).get_heads()
    assert len(heads) == 1, f"迁移链存在多个 head，upgrade head 会失败：{heads}"


def test_revision_graph_is_complete():
    """每个 down_revision 引用的修订都必须真实存在"""
    cfg = _alembic_config("/tmp/__never_used__.db")
    script = ScriptDirectory.from_config(cfg)
    revisions = {r.revision for r in script.walk_revisions()}
    for rev in revisions:
        node = script.get_revision(rev)
        for parent in (node.down_revision if isinstance(node.down_revision, tuple) else [node.down_revision]):
            if parent is None:
                continue  # 根迁移
            assert parent in revisions, f"{rev} 引用了不存在的上游 {parent}"


def test_greenfield_upgrade_creates_full_schema(empty_db):
    command.upgrade(_alembic_config(empty_db), "head")

    from app.core.database import Base
    import app.models  # noqa: F401  确保全部模型已注册

    inspector = inspect(create_engine(f"sqlite:///{empty_db}"))
    db_tables = set(inspector.get_table_names())
    meta_tables = set(Base.metadata.tables)

    assert not (meta_tables - db_tables), f"迁移没有建出的表：{sorted(meta_tables - db_tables)}"

    drift = {}
    for table in sorted(meta_tables & db_tables):
        model_cols = {c.name for c in Base.metadata.tables[table].columns}
        db_cols = {c["name"] for c in inspector.get_columns(table)}
        if model_cols != db_cols:
            drift[table] = {"model_only": sorted(model_cols - db_cols), "db_only": sorted(db_cols - model_cols)}
    assert not drift, f"模型与迁移存在列漂移：{drift}"


def test_upgrade_is_idempotent(empty_db):
    cfg = _alembic_config(empty_db)
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")  # 重复执行不应报错


def test_downgrade_to_base_then_reupgrade(empty_db):
    """回退到根迁移再全量升级，链路必须可逆"""
    cfg = _alembic_config(empty_db)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "20000101_000_base_schema")
    command.upgrade(cfg, "head")


def test_seed_data_is_idempotent_and_fk_safe(empty_db):
    cfg = _alembic_config(empty_db)
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")

    import sqlite3

    con = sqlite3.connect(empty_db)
    try:
        docs = con.execute("SELECT COUNT(*) FROM knowledge_documents").fetchone()[0]
        chunks = con.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
        assert docs == 5, f"播种文档数应为 5，实际 {docs}（幂等性被破坏）"
        assert chunks > 0

        dangling = con.execute(
            "SELECT COUNT(*) FROM knowledge_documents kd "
            "LEFT JOIN forklift_models fm ON kd.forklift_model_id = fm.id "
            "WHERE kd.forklift_model_id IS NOT NULL AND fm.id IS NULL"
        ).fetchone()[0]
        assert dangling == 0, "播种数据产生了悬挂外键（车型主键硬编码且未校验）"
    finally:
        con.close()


def test_auth_required_columns_exist(empty_db):
    """认证链路依赖的列必须真实存在，否则 get_current_user 一查就崩"""
    command.upgrade(_alembic_config(empty_db), "head")
    inspector = inspect(create_engine(f"sqlite:///{empty_db}"))
    columns = {c["name"] for c in inspector.get_columns("users")}
    for column in ("phone", "is_active", "email"):
        assert column in columns, f"users.{column} 缺失，认证链路会直接失败"
    assert inspector.get_unique_constraints("users") or "phone" in columns


VERSIONS_DIR = ROOT / "alembic" / "versions"


def _migration_sources():
    for path in sorted(VERSIONS_DIR.glob("*.py")):
        yield path, path.read_text(encoding="utf-8")


def test_no_migration_reads_the_app_global_engine():
    """迁移必须用 op.get_bind()。历史实现直接 import app 全局 engine，
    在 CI/部署环境会把数据写进开发库。"""
    offenders = []
    for path, text in _migration_sources():
        if re.search(r"from\s+app\.core\.database\s+import[^#\n]*\bengine\b", text):
            offenders.append(path.name)
    assert not offenders, f"迁移仍在读 app 全局 engine：{offenders}"


def test_no_sqlite_only_datetime_defaults():
    """datetime('now') 在 PostgreSQL 不存在，部署会炸；统一用 CURRENT_TIMESTAMP"""
    offenders = []
    for path, text in _migration_sources():
        if re.search(r"sa\.func\.datetime\(\s*['\"]now['\"]\s*\)", text):
            offenders.append(path.name)
    assert not offenders, f"迁移仍使用 SQLite 专属默认值：{offenders}"


def test_every_migration_declares_both_upgrade_and_downgrade():
    missing = []
    for path, text in _migration_sources():
        if not re.search(r"^def upgrade\b", text, re.M) or not re.search(r"^def downgrade\b", text, re.M):
            missing.append(path.name)
    assert not missing, f"缺少 upgrade/downgrade 的迁移：{missing}"
