"""把已有知识库文档 / 故障树写入 Qdrant，向量化用 WeMM。

运行:  python -m scripts.ingest_knowledge
"""
import sys
from pathlib import Path

# 让脚本可以直接以 `python scripts/ingest_knowledge.py` 方式运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal
from app.models.ai import KnowledgeDocument, KnowledgeChunk, FaultTree
from app.services.embedding_service import get_text_embedding
from app.core.vector_store import ensure_collection, upsert_point, COLLECTION


def ingest_chunks(db) -> int:
    rows = (
        db.query(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .all()
    )
    n = 0
    for chunk, doc in rows:
        text = chunk.chunk_text or ""
        if not text.strip():
            continue
        vec = get_text_embedding(text)
        payload = {
            "doc_id": doc.id,
            "chunk_id": chunk.id,
            "forklift_model_id": doc.forklift_model_id,
            "engine_model_id": doc.engine_model_id,
            "title": doc.title,
            "text": text,
            "url": doc.source,
        }
        upsert_point(point_id=f"chunk-{chunk.id}", vector=vec, payload=payload)
        n += 1
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
        c = ingest_chunks(db)
        f = ingest_faults(db)
        print(f"ingested chunks={c} faults={f} into {COLLECTION}")
    finally:
        db.close()


if __name__ == "__main__":
    main()