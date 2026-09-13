"""多语 MiniLM 检索器(384 维)。

与 WeMM(1024 维)并行,作为 _retrieve_context 的第二召回源。

设计:
  - 首次调用时从 knowledge_chunks + knowledge_documents 加载所有未过期文档,
    用 paraphrase-multilingual-MiniLM-L12-v2 编码,写入内存向量集合
    `forklift_zh_minilm`(与 ingest_6_docs.py 同一集合,保证 ID 体系一致)。
  - 后续调用直接复用缓存,毫秒级响应。
  - DB 内容变化时调用 invalidate() 清缓存,下次重新加载。
  - 过滤 license_expire 已过期的文档(与 WeMM 路径一致)。
  - 支持 forklift_model_id 过滤。

模型维度: 384(与 WeMM 1024 不冲突,故新建独立 collection)。
"""
from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

COLLECTION = "forklift_zh_minilm"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384

_lock = threading.Lock()
_loaded = False
_model: Any | None = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("loading MiniLM embedder: %s", EMBED_MODEL)
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def invalidate() -> None:
    """清缓存并清空内存集合,下次 retrieve() 重新加载 + 重新编码。

    只置 _loaded=False 会留下已删除文档的旧点(重建时只 upsert 不删除),
    所以这里同时清空集合,保证失效后集合与数据库严格一致。
    """
    global _loaded
    with _lock:
        _loaded = False
    from app.core.memory_vector_store import clear_collection

    clear_collection(COLLECTION)


def _load_all(db) -> int:
    """从 DB 加载所有未过期 doc + chunks,嵌入并写入内存集合。返回 chunk 数。"""
    from app.models.ai import KnowledgeDocument, KnowledgeChunk
    from app.models.copyright_mixin import license_active_condition, naive_utc_now
    from app.core.memory_vector_store import (
        ensure_collection,
        upsert_point as mem_upsert,
    )

    ensure_collection(COLLECTION)
    model = _get_model()

    rows = (
        db.query(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .filter(license_active_condition(KnowledgeDocument.license_expire))
        .all()
    )
    logger.info("MiniLM retriever: loading %d chunks from DB", len(rows))

    texts = [c.chunk_text for c, _ in rows if (c.chunk_text or "").strip()]
    if not texts:
        return 0
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    for (chunk, doc), vec in zip(rows, vecs):
        text = chunk.chunk_text or ""
        if not text.strip():
            continue
        mem_upsert(
            point_id=f"minilm-chunk-{chunk.id}",
            vector=vec.tolist(),
            payload={
                "doc_id": doc.id,
                "chunk_id": chunk.id,
                "forklift_model_id": doc.forklift_model_id,
                "engine_model_id": doc.engine_model_id,
                "title": doc.title,
                "category": doc.category or "",
                "doc_type": doc.doc_type or "",
                "text": text,
                "url": doc.source or "",
                "page_number": chunk.page_number,
                "section_title": (chunk.section_title or "")[:200],
            },
            collection_name=COLLECTION,
        )
    return len(texts)


def ensure_loaded(db) -> bool:
    """若未加载,加载一次。返回 True 表示本调用做了首次加载。"""
    global _loaded
    if _loaded:
        return False
    with _lock:
        if _loaded:
            return False
        _load_all(db)
        _loaded = True
    return True


def retrieve(
    query: str,
    db,
    top_k: int = 5,
    forklift_model_id: int | None = None,
    engine_model_id: int | None = None,
) -> list[dict]:
    """同进程检索 MiniLM 集合,返回 [{id, score, payload}, ...]。"""
    from app.core.memory_vector_store import search_similar as mem_search

    ensure_loaded(db)
    model = _get_model()
    vec = model.encode([query], normalize_embeddings=True)[0].tolist()
    hits = mem_search(
        vec,
        top_k=top_k,
        collection_name=COLLECTION,
        forklift_model_id=forklift_model_id,
        engine_model_id=engine_model_id,
    )
    return [
        {"id": h["id"], "score": h["score"], "payload": h.get("payload", {})}
        for h in hits
    ]


def format_for_prompt(hits: list[dict], max_chars: int = 300) -> str:
    """把召回结果格式化为可拼到 system_prompt 的文本。"""
    if not hits:
        return ""
    lines = []
    for h in hits:
        p = h.get("payload", {})
        title = p.get("title", "")
        text = (p.get("text", "") or "")[:max_chars]
        url = p.get("url", "")
        cite = f" [来源: {url}]" if url else ""
        section = p.get("section_title", "")
        if section:
            section = f"《{section}》"
        lines.append(f"- {title}{section}: {text}{cite}")
    return "\n".join(lines)
