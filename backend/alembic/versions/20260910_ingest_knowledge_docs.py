"""ingest initial knowledge documents into knowledge_documents table

Revision ID: 20260910_ingest_knowledge_docs
Revises: 20260914_add_manual_metadata
Create Date: 2026-09-10

本修订是数据播种步骤，已移到迁移链最末尾：它通过 ORM 模型插入行，若排在
后续加列迁移之前，回退再升级时模型字段与库表结构不一致会直接报错。

幂等：按 (title, source) 去重，只补充缺失的文档与其切片；不会清空库里已有的知识内容。

"""
from datetime import datetime, timezone

from alembic import op
from sqlalchemy.orm import Session

from app.models import *  # noqa: F401,F403  确保全部模型已注册到 Base.metadata


revision = '20260910_ingest_knowledge_docs'
down_revision = '20260914_add_manual_metadata'
branch_labels = None
depends_on = None


# 初始知识文档。forklift_model_id / engine_model_id 是 seed 数据里的期望主键，
# 目标库若不存在对应车型/发动机则置 NULL，而不是关闭外键约束硬插悬挂引用。
INITIAL_KNOWLEDGE_DOCS = [
    {
        "title": "龙工LG30型号维修手册",
        "content": "龙工LG30内燃式叉车维修手册。内容包括：1. 发动机部分：发动机型号、缸径、活塞、活塞环、曲轴、连杆等部件的结构、功用及检查、维修要求及更换标准。2. 传动部分：变速箱、传动轴、主减速器、桥壳等部件的结构、功用及检查、维修要求及更换标准。3. 液压部分：液压油缸、马达、阀组等部件的结构、功用及检查、维修要求及更换标准。4. 电气部分：蓄电池、发电机、调节器等部件的结构、功用及检查、维修要求及更换标准。5. 底盘部分：转向桥、驱动桥、车架等部件的结构、功用及检查、维修要求及更换标准。6. 附件部分：货叉、油缸等部件的结构、功用及检查、维修要求及更换标准。",
        "source": "https://cdn.example.com/knowledge/manuals/longgong-lg30.pdf",
        "doc_type": "manual",
        "forklift_model_id": 1,
        "engine_model_id": 1,
        "commercial_use": 0,
        "copyright_owner": "龙工叉车有限公司",
        "license_type": "licensed",
        "license_expire": None,
    },
    {
        "title": "丰田7FGQ型号故障代码集",
        "content": "丰田叉车常见故障代码及处理方法。1. 发动机故障代码：001-099之间，涵盖活塞、气缸、燃烧室等问题。2. 液压故障代码：100-199之间，涵盖液压油、油缸、马达等问题。3. 电气故障代码：200-299之间，涵盖蓄电池、发电机、传感器等问题。4. 传动故障代码：300-399之间，涵盖变速箱、传动轴等问题。5. 底盘故障代码：400-499之间，涵盖转向、驱动等问题。6. 安全故障代码：500-599之间，涵盖安全装置、传感器等问题。",
        "source": "https://cdn.example.com/knowledge/faultcodes/towng-7fqn.txt",
        "doc_type": "fault",
        "forklift_model_id": 2,
        "engine_model_id": 2,
        "commercial_use": 0,
        "copyright_owner": "丰田自动车有限公司",
        "license_type": "licensed",
        "license_expire": None,
    },
    {
        "title": "合力CPA型号故障树数据库",
        "content": "合力CPA系列叉车典型故障树数据库。1. 发动机故障：起动困难、油耗过高、动力不足等。2. 液压故障：举升缓慢、倾斜不良、下降不稳定等。3. 电气故障：仪表不显示、起动机不转、灯光异常等。4. 传动故障：换档困难、打滑、噪音等。5. 底盘故障：转向沉重、制动拖滞、轮胎磨损等。6. 附件故障：货叉变形、销子断裂、油缸泄漏等。"
        "每个故障树包括：症状、原因（列表）、解决方案（列表）和概率（字典）。",
        "source": "https://cdn.example.com/knowledge/faulttrees/heli-cpa.json",
        "doc_type": "case",
        "forklift_model_id": 3,
        "engine_model_id": 3,
        "commercial_use": 0,
        "copyright_owner": "合力叉车有限公司",
        "license_type": "licensed",
        "license_expire": None,
    },
    {
        "title": "杭叉CDD型号技术参数",
        "content": "杭叉CDD系列电动叉车技术参数。规格：额定起重量：1.5-3.0吨，内燃版本额定起重量：3.0-5.0吨。货叉尺寸：900-1500mm，载荷中心：500-600mm，离地间隙：120-200mm。发动机参数：排量、功率、油耗等。传动系统：变速箱类型、主减速器比速。液压系统：举升泵、倾斜泵、马达、阀组。电气系统：蓄电池规格、充电系统、仪表盘。底盘系统：轮胎规格、转向系统、制动系统。安全装置：限位器、报警器、防护罩等。",
        "source": "https://cdn.example.com/knowledge/specs/hangcha-cdd.pdf",
        "doc_type": "parameter",
        "forklift_model_id": 4,
        "engine_model_id": None,
        "commercial_use": 0,
        "copyright_owner": "杭州叉车有限公司",
        "license_type": "licensed",
        "license_expire": None,
    },
    {
        "title": "林德STACITY故障诊断案例",
        "content": "林德电动叉车STACITY典型故障诊断案例。1. 举升系统故障：起升缓慢、起升不到位、自动下降。2. 倾斜系统故障：倾斜速度慢、倾斜不到位、自动倾斜。3. 驱动系统故障：运行速度慢、运行无力、无法运行。4. 转向系统故障：转向沉重、转向不灵、自动偏向。5. 制动系统故障：制动距离长、制动拖滞、制动噪音。6. 电气系统故障：仪表不显示、起动机不转、充电异常。每个案例包括：症状、可能原因、检查步骤、维修建议、预防措施。",
        "source": "https://cdn.example.com/knowledge/cases/linde-stacity.txt",
        "doc_type": "case",
        "forklift_model_id": 5,
        "engine_model_id": None,
        "commercial_use": 0,
        "copyright_owner": "林德叉车有限公司",
        "license_type": "licensed",
        "license_expire": None,
    },
]


def _session() -> Session:
    """绑定到本次迁移的连接，而不是 app 的全局 engine。

    历史实现直接用 `app.core.database.engine`，导致在 CI/部署环境对迁移目标库执行
    本步骤时，实际读写的是开发库。
    """
    return Session(bind=op.get_bind())


def _resolve_fk(session: Session, table, expected_id):
    if expected_id is None:
        return None
    return expected_id if session.query(table.id).filter(table.id == expected_id).first() else None


def _split_chunks(content: str, doc_id: int):
    for i, part in enumerate(str(content).split("。")):
        text = part.strip()
        if text:
            yield KnowledgeChunk(
                document_id=doc_id,
                chunk_index=i,
                chunk_text=text + "。",
                embedding_id=f"ingest-chunk-{doc_id}-{i}",
            )


def upgrade() -> None:
    session = _session()
    try:
        existing = {
            (row.title, row.source)
            for row in session.query(KnowledgeDocument.title, KnowledgeDocument.source).all()
        }

        inserted_docs = []
        for data in INITIAL_KNOWLEDGE_DOCS:
            key = (data["title"], data["source"])
            if key in existing:
                continue
            doc = KnowledgeDocument(
                title=data["title"],
                content=data["content"],
                source=data["source"],
                doc_type=data["doc_type"],
                forklift_model_id=_resolve_fk(session, ForkliftModel, data["forklift_model_id"]),
                engine_model_id=_resolve_fk(session, EngineModel, data["engine_model_id"]),
                commercial_use=data["commercial_use"],
                copyright_owner=data["copyright_owner"],
                license_type=data["license_type"],
                license_expire=data["license_expire"],
                created_at=datetime.now(timezone.utc),
            )
            session.add(doc)
            existing.add(key)
            inserted_docs.append(doc)

        chunk_count = 0
        if inserted_docs:
            session.flush()  # 取回自增主键，用于挂切片
            for doc in inserted_docs:
                for chunk in _split_chunks(doc.content, doc.id):
                    session.add(chunk)
                    chunk_count += 1

        session.commit()
        print(f"[{revision}] knowledge docs: +{len(inserted_docs)}, chunks: +{chunk_count}")
    finally:
        session.close()


def downgrade() -> None:
    """只回退本迁移插入的文档，不影响其它知识内容。"""
    session = _session()
    try:
        titles = tuple(data["title"] for data in INITIAL_KNOWLEDGE_DOCS)
        rows = session.query(KnowledgeDocument.id).filter(KnowledgeDocument.title.in_(titles)).all()
        doc_ids = [row.id for row in rows]
        if doc_ids:
            session.query(KnowledgeChunk).filter(KnowledgeChunk.document_id.in_(doc_ids)).delete(
                synchronize_session=False
            )
            session.query(KnowledgeDocument).filter(KnowledgeDocument.id.in_(doc_ids)).delete(
                synchronize_session=False
            )
        session.commit()
    finally:
        session.close()
