"""知识库文档分块与向量索引同步。"""
from __future__ import annotations

import logging

from app.core.hybrid_retriever import invalidate as invalidate_hybrid
from app.core.vector_store import delete_by_document, upsert_point
from app.models.ai import KnowledgeChunk, KnowledgeDocument
from app.models.copyright_mixin import is_license_expired
from app.services.embedding_service import get_text_embedding

logger = logging.getLogger(__name__)


def _split_content(content: str) -> list[str]:
    parts = []
    for part in (content or "").replace("\r\n", "\n").split("。"):
        text = part.strip()
        if text:
            parts.append(text + "。")
    return parts


def _payload(chunk: KnowledgeChunk, doc: KnowledgeDocument) -> dict:
    return {
        "doc_id": doc.id,
        "chunk_id": chunk.id,
        "forklift_model_id": doc.forklift_model_id,
        "engine_model_id": doc.engine_model_id,
        "title": doc.title,
        "category": doc.category or "",
        "doc_type": doc.doc_type or "",
        "text": chunk.chunk_text or "",
        "url": doc.source or "",
        "page_number": chunk.page_number,
        "section_title": (chunk.section_title or "")[:200],
    }


def sync_document_index(
    db,
    document_id: int,
    rebuild_chunks: bool = False,
) -> int:
    """同步一个文档的数据库分块、WeMM 向量和混合检索缓存。"""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if doc is None:
        return 0

    if rebuild_chunks:
        db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document_id).delete()
        for index, text in enumerate(_split_content(doc.content or "")):
            db.add(KnowledgeChunk(document_id=document_id, chunk_index=index, chunk_text=text))
        db.commit()
        db.refresh(doc)

    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.document_id == document_id)
        .order_by(KnowledgeChunk.chunk_index.asc())
        .all()
    )
    delete_by_document(document_id)
    count = 0
    if not is_license_expired(doc.license_expire):
        for chunk in chunks:
            text = chunk.chunk_text or ""
            if not text.strip():
                continue
            upsert_point(
                point_id=f"chunk-{chunk.id}",
                vector=get_text_embedding(text),
                payload=_payload(chunk, doc),
            )
            count += 1
    invalidate_hybrid()
    logger.info("knowledge index synced: document_id=%s chunks=%s", document_id, count)
    return count


def delete_document_index(document_id: int) -> int:
    """删除文档在向量库中的全部点并使混合检索缓存失效。"""
    count = delete_by_document(document_id)
    invalidate_hybrid()
    return count
