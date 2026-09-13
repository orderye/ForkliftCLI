"""BM25 + MiniLM 混合召回。

问题:MiniLM-L12 对中文技术术语的细粒度语义区分弱。例如:
  Q = "液压油 32号 46号 更换周期"
  错召回: CPC 供油泵零件图(图名含"供油""油")
  应召回: 龙工液压系统维护指南(含"32号""46号""更换周期")

修法:叠加 BM25 关键词召回,与 MiniLM 向量召回用 RRF 合并。

设计:
  - 首次调用时从 DB 加载所有未过期 chunk,构建 BM25 索引
  - 中文分词用字符 bigram(无需 jieba 等重依赖)
  - RRF 公式: score = sum(1 / (k + rank_i))  对每路 top-K 的命中
  - 复用 minilm_retriever 的内存向量集合,共享懒加载缓存
"""
from __future__ import annotations

import logging
import re
import threading
from typing import Any

from app.core.minilm_retriever import (
    COLLECTION,
    invalidate as minilm_invalidate,
)
from app.core.memory_vector_store import (
    search_similar as mem_search,
)

logger = logging.getLogger(__name__)

# RRF 常数(经验值 60)
RRF_K = 60
# 各路返回的 top 大小
TOP_K_PER = 20
# 最终返回
TOP_N = 5

_lock = threading.Lock()
_loaded = False
_bm25: Any | None = None
_corpus_tokens: list[list[str]] = []
_chunk_ids: list[int] = []
_doc_ids: list[int] = []
_payloads: list[dict] = []


def invalidate() -> None:
    """清缓存,下次 retrieve() 重新加载 BM25 索引 + MiniLM 集合。"""
    global _loaded
    with _lock:
        _loaded = False
        _bm25 = None
        _corpus_tokens = []
        _chunk_ids = []
        _doc_ids = []
        _payloads = []
    minilm_invalidate()


# ── 中文分词(字符 bigram) ──────────────────────────────────────
_KEEP_CHINESE = re.compile(r"[\u4e00-\u9fff]+")
_KEEP_ALNUM = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(text: str) -> list[str]:
    """字符 bigram + 英文/数字 token,简单但对中文技术词足够。"""
    text = text or ""
    tokens: list[str] = []
    # 连续汉字 → 相邻 bigram
    for m in _KEEP_CHINESE.finditer(text):
        s = m.group(0)
        if len(s) == 1:
            tokens.append(s)
        else:
            tokens.extend(s[i : i + 2] for i in range(len(s) - 1))
    # 英文/数字词
    tokens.extend(m.group(0).lower() for m in _KEEP_ALNUM.finditer(text))
    return tokens


def _ensure_bm25_loaded(db) -> None:
    """从 DB 加载 chunk,构建 BM25 索引。"""
    global _loaded, _bm25, _corpus_tokens, _chunk_ids, _doc_ids, _payloads
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        from rank_bm25 import BM25Okapi
        from app.models.ai import KnowledgeChunk, KnowledgeDocument
        from app.models.copyright_mixin import license_active_condition

        rows = (
            db.query(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .filter(license_active_condition(KnowledgeDocument.license_expire))
            .all()
        )
        _chunk_ids = [c.id for c, _ in rows]
        _doc_ids = [d.id for _, d in rows]
        _payloads = [
            {
                "doc_id": d.id,
                "chunk_id": c.id,
                "forklift_model_id": d.forklift_model_id,
                "engine_model_id": d.engine_model_id,
                "title": d.title,
                "category": d.category or "",
                "doc_type": d.doc_type or "",
                "text": c.chunk_text or "",
                "url": d.source or "",
                "page_number": c.page_number,
                "section_title": (c.section_title or "")[:200],
            }
            for c, d in rows
        ]
        _corpus_tokens = [_tokenize(p["text"]) for p in _payloads]
        if _corpus_tokens:
            _bm25 = BM25Okapi(_corpus_tokens)
        else:
            _bm25 = None
        _loaded = True
        logger.info(
            "Hybrid retriever: BM25 index built, %d chunks", len(_corpus_tokens)
        )


def _bm25_search(
    query: str,
    forklift_model_id: int | None,
    engine_model_id: int | None,
    top_k: int,
) -> list[dict]:
    if _bm25 is None:
        return []
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []
    scores = _bm25.get_scores(q_tokens)
    # 按分数降序,跳过过滤掉的 doc
    indexed: list[tuple[int, float]] = []
    for i, s in enumerate(scores):
        if s <= 0:
            continue
        if forklift_model_id is not None and _payloads[i]["forklift_model_id"] != forklift_model_id:
            continue
        if engine_model_id is not None and _payloads[i]["engine_model_id"] != engine_model_id:
            continue
        indexed.append((i, float(s)))
    indexed.sort(key=lambda x: x[1], reverse=True)
    out = []
    for rank, (i, s) in enumerate(indexed[:top_k], start=1):
        out.append({"rank": rank, "score": s, "index": i})
    return out


def _minilm_search(
    db,
    query: str,
    forklift_model_id: int | None,
    engine_model_id: int | None,
    top_k: int,
) -> list[dict]:
    """从已加载的内存向量集合检索。"""
    from app.core.minilm_retriever import ensure_loaded, _get_model

    ensure_loaded(db)
    model = _get_model()
    vec = model.encode([query], normalize_embeddings=True)[0].tolist()
    hits = mem_search(
        vec,
        top_k=top_k * 3,  # 多取一些,后面按 fmid 过滤后再截
        collection_name=COLLECTION,
        forklift_model_id=forklift_model_id,
        engine_model_id=engine_model_id,
    )
    # 在 _payloads 里按 chunk_id 找到 index
    chunk_to_idx = {p["chunk_id"]: idx for idx, p in enumerate(_payloads)}
    out = []
    for rank, h in enumerate(hits, start=1):
        cid = h.get("payload", {}).get("chunk_id")
        if cid is None:
            continue
        idx = chunk_to_idx.get(cid)
        if idx is None:
            continue
        out.append({"rank": rank, "score": h.get("score", 0), "index": idx})
    return out[:top_k]


def _rrf_merge(
    bm25_hits: list[dict], minilm_hits: list[dict], k: int = RRF_K
) -> list[dict]:
    """Reciprocal Rank Fusion: score = sum(1 / (k + rank_i))"""
    rrf: dict[int, float] = {}
    src: dict[int, list[str]] = {}
    for h in bm25_hits:
        idx = h["index"]
        rrf[idx] = rrf.get(idx, 0) + 1.0 / (k + h["rank"])
        src.setdefault(idx, []).append("bm25")
    for h in minilm_hits:
        idx = h["index"]
        rrf[idx] = rrf.get(idx, 0) + 1.0 / (k + h["rank"])
        src.setdefault(idx, []).append("minilm")
    merged = sorted(rrf.items(), key=lambda x: x[1], reverse=True)
    return [
        {"index": idx, "rrf_score": sc, "from": src.get(idx, [])}
        for idx, sc in merged
    ]


def retrieve(
    query: str,
    db,
    top_n: int = TOP_N,
    forklift_model_id: int | None = None,
    engine_model_id: int | None = None,
) -> list[dict]:
    """混合召回:BM25 + MiniLM,RRF 合并。

    engine_model_id 用于 BM25 和 MiniLM 检索结果过滤。
    """
    _ensure_bm25_loaded(db)
    bm25_hits = _bm25_search(query, forklift_model_id, engine_model_id, TOP_K_PER)
    minilm_hits = _minilm_search(db, query, forklift_model_id, engine_model_id, TOP_K_PER)
    merged = _rrf_merge(bm25_hits, minilm_hits)

    out = []
    for m in merged[:top_n]:
        idx = m["index"]
        p = _payloads[idx]
        out.append(
            {
                "id": f"hybrid-{p['chunk_id']}",
                "score": m["rrf_score"],
                "rrf_score": m["rrf_score"],
                "from": m["from"],
                "payload": p,
            }
        )
    return out


def format_for_prompt(hits: list[dict], max_chars: int = 300) -> str:
    """把混合召回结果格式化为可拼到 system_prompt 的文本。"""
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
        src = "+".join(h.get("from", []))
        lines.append(f"- [{src}] {title}{section}: {text}{cite}")
    return "\n".join(lines)
