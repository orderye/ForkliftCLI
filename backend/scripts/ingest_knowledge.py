"""把已有知识库文档 / 故障树写入向量库（WeMM），并重建混合检索缓存。

知识文档复用 app.services.knowledge_index_service.sync_document_index：
  - 重建数据库分块（与 CRUD 保持同一分块逻辑）
  - 过滤授权过期文档
  - 删除旧点后重建 WeMM 向量
  - 失效 BM25/MiniLM 混合检索缓存

运行:  python -m scripts.ingest_knowledge
"""
import sys
from pathlib import Path

# 让脚本可以直接以 `python scripts/ingest_knowledge.py` 方式运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal
from app.models.ai import KnowledgeDocument, FaultTree
from app.core.vector_store import ensure_collection, upsert_point, COLLECTION
from app.services.embedding_service import get_text_embedding
from app.services.knowledge_index_service import sync_document_index


def ingest_documents(db) -> int:
    """按统一索引服务重建所有知识文档的向量索引。返回写入分片数。"""
    doc_ids = [row.id for row in db.query(KnowledgeDocument.id).all()]
    n = 0
    for document_id in doc_ids:
        n += sync_document_index(db, document_id, rebuild_chunks=True)
    return n


def _causes_text(causes_json) -> str:
    if not causes_json:
        return ""
    if isinstance(causes_json, list):
        return " ".join(str(c) for c in causes_json)
    return str(causes_json)


def ingest_faults(db) -> int:
    trees = db.query(FaultTree).all()
    n = 0
    for t in trees:
        parts = [t.symptom or "", _causes_text(t.causes_json)]
        text = " ".join(p for p in parts if p)
        if not text.strip():
            continue
        vec = get_text_embedding(text)
        payload = {
            "fault_id": t.id,
            "forklift_model_id": t.forklift_model_id,
            "engine_model_id": t.engine_model_id,
            "symptom": t.symptom,
            "title": f"故障: {t.symptom[:60]}",
            "text": text,
            "url": "",
        }
        upsert_point(point_id=f"fault-{t.id}", vector=vec, payload=payload)
        n += 1
    return n


def main() -> None:
    ensure_collection()
    db = SessionLocal()
    try:
        c = ingest_documents(db)
        f = ingest_faults(db)
        print(f"ingested chunks={c} faults={f} into {COLLECTION}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
