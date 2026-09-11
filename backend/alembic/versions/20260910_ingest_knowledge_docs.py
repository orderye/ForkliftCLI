"""ingest initial knowledge documents into knowledge_documents table

Revision ID: 20260910_ingest_knowledge_docs
Revises: 20260910_merge_heads
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.core.database import engine, Base
from app.models import *
import csv
import os
from datetime import datetime, timezone


revision = '20260910_ingest_knowledge_docs'
down_revision = '20260910_merge_heads'
branch_labels = None
depends_on = None


# 初始知识文档数据
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
        "created_at": datetime.now(timezone.utc)
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
        "created_at": datetime.now(timezone.utc)
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
        "created_at": datetime.now(timezone.utc)
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
        "created_at": datetime.now(timezone.utc)
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
        "created_at": datetime.now(timezone.utc)
    }
]


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")
    
    session = Session(bind=engine)
    try:
        # 清空可能已存在的数据
        session.query(KnowledgeDocument).delete()
        session.query(KnowledgeChunk).delete()
        session.commit()
        
        # 插入知识文档
        for doc_data in INITIAL_KNOWLEDGE_DOCS:
            doc = KnowledgeDocument(**doc_data)
            session.add(doc)
            
        session.commit()
        
        # 为每个文档创建切片
        for doc in INITIAL_KNOWLEDGE_DOCS:
            doc_id = doc["id"] = session.query(KnowledgeDocument).filter_by(
                title=doc["title"],
                source=doc["source"]
            ).first().id
            
            # 创建2-3个切片
            chunks = []
            content_parts = doc["content"].split("。")
            for i, part in enumerate(content_parts):
                if part.strip():
                    chunk = KnowledgeChunk(
                        document_id=doc_id,
                        chunk_index=i,
                        chunk_text=part.strip() + "。",
                        embedding_id=f"""ingest-chunk-{doc_id}-{i}"""
                    )
                    session.add(chunk)
                    
            session.commit()
            
    finally:
        session.close()
        op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")
    
    session = Session(bind=engine)
    try:
        session.query(KnowledgeChunk).delete()
        session.query(KnowledgeDocument).delete()
        session.commit()
    finally:
        session.close()
        op.execute("PRAGMA foreign_keys=ON")