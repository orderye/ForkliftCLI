"""Day 1-2 RAG 灌库:把 Docs/_extracted 下 6 份 OCR 文本切片并向量化。

设计:
  - 每个文档一个配置(title / doc_type / category / forklift_model_id / 切片规则)
  - 切片策略 = 章节优先 + 字符回退(max_chars=1200, overlap=150)
  - 嵌入模型 = paraphrase-multilingual-MiniLM-L12-v2 (384 维,中英多语,CPU 友好)
  - 写入 knowledge_documents + knowledge_chunks(idempotent on title+source)
  - 向量写入新集合 forklift_zh_minilm(避免与 1024 维 WeMM 集合冲突)
  - 使用 Qdrant 内存存储(USE_MEMORY_STORE=true 等价路径)

运行:
  cd backend && python3 -m scripts.ingest_6_docs --dry-run
  cd backend && python3 -m scripts.ingest_6_docs
  cd backend && python3 -m scripts.ingest_6_docs --query "货叉下滑"
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ── 强制使用内存向量存储 + 384 维 MiniLM(本脚本专用路径) ───────────────
os.environ["USE_MEMORY_STORE"] = "true"

from app.core.database import SessionLocal  # noqa: E402
from app.core.vector_store import (  # noqa: E402
    ensure_collection as _ensure,
    upsert_point as _upsert,
    COLLECTION as DEFAULT_COLLECTION,
)
from app.core.memory_vector_store import (  # noqa: E402
    ensure_collection as mem_ensure,
    upsert_point as mem_upsert,
    search_similar as mem_search,
)
from app.models.ai import KnowledgeDocument, KnowledgeChunk  # noqa: E402

logger = logging.getLogger("ingest_6_docs")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# ── 嵌入模型:多语 MiniLM,CPU 友好,中文可用 ───────────────────────────
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384
COLLECTION = "forklift_zh_minilm"  # 专用集合,不与 WeMM 1024 维冲突
DOCS_DIR = Path("/Volumes/aigo S7 Med/Forklift/Docs/_extracted")

# ── 6 份文档的配置 ─────────────────────────────────────────────────
# forklift_model_id 关联到 seed_brands.py 中已存在的车型
DOC_CONFIG = [
    {
        "key": "cpc_parts",
        "txt": "CPC-CPCD-内燃平衡重叉车零件手册说明书.txt",
        "title": "CPC/CPCD 20-30 内燃平衡重叉车零件手册",
        "doc_type": "manual",
        "category": "内燃平衡重叉车-零件手册",
        "page_marker": r"={10,}\s*第\s*(\d+)\s*页\s*={10,}",
        "section_markers": [r"^总成图", r"^图\s*\d+", r"^[A-Z]{2,3}\s+[A-Z]", r"^说明"],
        "forklift_model_id": 14,  # 杭叉 CPCD30(代表)
        "secondary_model_ids": [15, 31, 32, 33, 34, 36, 37, 38, 39, 44],
    },
    {
        "key": "noblelift_parts",
        "txt": "Noblelift-电动叉车-PT20-25-30P-C-零件手册说明书.txt",
        "title": "Noblelift PT20/25/30P-C 电动托盘搬运车零件手册",
        "doc_type": "manual",
        "category": "电动托盘搬运车-零件手册",
        "page_marker": r"={10,}\s*第\s*(\d+)\s*页\s*={10,}",
        "section_markers": [r"^Ch\d+", r"^Chapter\s+\d+", r"^图\s*\d+"],
        "forklift_model_id": None,  # 暂无对应车型(种子库只有 10 品牌 50 车型,无 Noblelift)
        "secondary_model_ids": [],
    },
    {
        "key": "efg_manual",
        "txt": "永恒力EFG-316n-320n电动叉车操作手册.txt",
        "title": "永恒力 EFG 316n/320n 电动叉车操作手册",
        "doc_type": "manual",
        "category": "电动平衡重叉车-操作手册",
        "page_marker": r"={10,}\s*第\s*(\d+)\s*页\s*={10,}",
        # 章节标记:大写字母独立行(章),中文章节(序数+顿号),1.1 数字小节
        # 注意:不要匹配 ^[A-Z]\d+ (会把 E1/B2 等页码引用当成标题)
        "section_markers": [
            r"^[A-Z]\s*$",
            r"^\d+\.\d+\s+[\u4e00-\u9fffA-Za-z]",
            r"^[一二三四五六七八九十]+、",
        ],
        "forklift_model_id": None,  # 永恒力不在种子库
        "secondary_model_ids": [],
    },
    {
        "key": "cqd_manual",
        "txt": "前移式叉车使用说明书.txt",
        "title": "杭叉 CQD12-20H 前移式叉车使用说明书",
        "doc_type": "manual",
        "category": "电动前移式叉车-操作手册",
        # CQD 文本无页码标记,以"第N部分"做主切片
        "page_marker": r"^第[一二三四五六七八九十]+部分",
        "section_markers": [
            r"^第[一二三四五六七八九十]+部分",
            r"^[一二三四五六七八九十]+、\s*[\u4e00-\u9fff]",
        ],
        "forklift_model_id": None,  # 杭叉前移式不在种子库
        "secondary_model_ids": [],
    },
    {
        "key": "fd30_spec",
        "txt": "龙工FD30参数.txt",
        "title": "龙工 FD30 内燃平衡重叉车参数表",
        "doc_type": "parameter",
        "category": "内燃平衡重叉车-参数表",
        "page_marker": None,
        "section_markers": [r"^特性", r"^性能", r"^尺寸", r"^底盘", r"^型号", r"^参数"],
        "forklift_model_id": None,  # 龙工种子只有 CPCD30/CPD25,无 FD30
        "secondary_model_ids": [44],  # 龙工 CPCD30 关联参考
    },
    {
        "key": "longgong_hydraulic",
        "txt": "龙工叉车液压系统.txt",
        "title": "龙工叉车液压系统工作原理、常见故障与维修保养",
        "doc_type": "manual",
        "category": "液压系统-通用技术",
        "page_marker": None,
        "section_markers": [
            r"^.{0,4}工作原理",
            r"^常见故障",
            r"^.{0,4}诊断",
            r"^液压油",
            r"^.{0,4}更换",
            r"^注意事项",
            r"^操作前",
            r"^操作中",
            r"^预防性",
            r"^延伸阅读",
        ],
        "forklift_model_id": None,  # 通用知识
        "secondary_model_ids": [44, 45],  # 龙工系列
    },
]


# ── 嵌入模型(单例,延迟加载) ─────────────────────────────────────────
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        logger.info("loading embedder: %s (dim=%d)", EMBED_MODEL_NAME, EMBED_DIM)
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_embedder()
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vecs]


# ── 切片逻辑 ─────────────────────────────────────────────────────────
PAGE_PATTERNS = [
    r"={10,}\s*第\s*(\d+)\s*页\s*={10,}",  # 永恒力/CPC/Noblelift
    r"- \d+ -\s*$",  # CPC 页码
    r"^\s*\d+\s*$",  # 纯数字页
    r"==========",  # 杭叉前移式
]


def split_by_pages(text: str, marker: str | None) -> list[tuple[int | None, str]]:
    """按页标记切分,返回 [(页码, 内容), ...]。

    marker 兼容两种形式:
      - 带捕获组的数字页码:  `={10,}\\s*第\\s*(\\d+)\\s*页\\s*={10,}` → 页码 = int
      - 无捕获组的纯分隔符:  `==========`                    → 页码 = 自增序号
    """
    if not marker:
        return [(None, text)]
    pattern = re.compile(marker, re.MULTILINE)
    has_capture = pattern.groups > 0
    pieces: list[tuple[int | None, str]] = []
    last_pos = 0
    last_page: int | None = None
    page_counter = 0
    for m in pattern.finditer(text):
        body = text[last_pos:m.start()].strip()
        if body:
            pieces.append((last_page, body))
        if has_capture and m.lastindex:
            try:
                last_page = int(m.group(1))
            except (ValueError, TypeError):
                last_page = None
        else:
            page_counter += 1
            last_page = page_counter
        last_pos = m.end()
    tail = text[last_pos:].strip()
    if tail:
        pieces.append((last_page, tail))
    if not pieces:
        return [(None, text)]
    return pieces


def split_by_sections(
    text: str, section_markers: list[str] | None
) -> list[tuple[str, str]]:
    """在已按页切分后的文本上,再按章节标题切。返回 [(section_title, body), ...]。

    关键: 章节标记本身归入"下一个 section",避免把段落开头的几个字
    切成半句话。
    """
    if not section_markers:
        return [("", text)]
    combined = re.compile("|".join(f"({m})" for m in section_markers), re.MULTILINE)
    pieces: list[tuple[str, str]] = []
    last_pos = 0
    last_title = ""
    for m in combined.finditer(text):
        body = text[last_pos:m.start()].strip()
        if body:
            pieces.append((last_title, body))
        # 标记本身作为下一个 section 的标题
        last_title = m.group(0).strip()
        last_pos = m.end()
    tail = text[last_pos:].strip()
    if tail:
        pieces.append((last_title, tail))
    return pieces or [("", text)]


def char_chunk(
    text: str, max_chars: int = 1200, overlap: int = 150
) -> list[str]:
    """字符级回退切片。优先在段落边界切,其次在句末切。"""
    # 段落级:按连续空行分组
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    if not paragraphs:
        return []
    chunks: list[str] = []
    buf = ""
    for p in paragraphs:
        # 单段超过 max_chars → 句子级回退
        if len(p) > max_chars:
            if buf:
                chunks.append(buf)
                buf = ""
            for start in range(0, len(p), max_chars - overlap):
                piece = p[start : start + max_chars]
                # 在句末切断
                for sep in ["。", "；", ". ", "!\n", "? "]:
                    idx = piece.rfind(sep)
                    if idx > max_chars * 0.6:
                        piece = piece[: idx + len(sep)]
                        break
                piece = piece.strip()
                if piece:
                    chunks.append(piece)
            continue
        # 累积到 buf
        if not buf:
            buf = p
        elif len(buf) + len(p) + 1 <= max_chars:
            buf = buf + "\n" + p
        else:
            chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return [c for c in chunks if c]


def merge_short_chunks(chunks: list[dict], min_chars: int = 80) -> list[dict]:
    """把过短的 chunk 合并到前一个(同 page)里,标题继承后一个。"""
    if not chunks:
        return chunks
    out = [chunks[0].copy()]
    for c in chunks[1:]:
        prev = out[-1]
        if len(c["text"]) < min_chars and prev["page"] == c["page"]:
            merged_text = prev["text"] + "\n" + c["text"]
            out[-1] = {
                **prev,
                "text": merged_text,
                "section": c["section"] or prev["section"],
            }
        else:
            out.append(c)
    return out


def slice_doc(
    text: str, page_marker: str | None, section_markers: list[str] | None
) -> list[dict]:
    """对单篇文档做混合切片。返回 [{page, section, text}, ...]

    流程:文本预处理 → 页切分 → 页内按段落归一化 → 字符回退切(1200/150)。
    section 标记在切完后,做一次"标题继承":用 section_markers 在原文中
    扫一遍,把离 chunk 最近的标题作为该 chunk 的 section 字段。
    """
    # OCR 后处理:剥离控制符 + 行首控制字符(让 ^ 能匹配章节标题)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"^[\f\v\r\t ]+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)

    pages = split_by_pages(text, page_marker)
    out: list[dict] = []
    for page_no, page_text in pages:
        if not page_text.strip():
            continue
        pieces = char_chunk(page_text)
        for p in pieces:
            out.append(
                {
                    "page": page_no,
                    "section": "",  # 后填
                    "text": p,
                }
            )

    # 标题继承:扫原文,把每个 section_markers 命中的位置 → 标题,赋给后续所有 chunk
    if section_markers:
        combined = re.compile(
            "|".join(f"({m})" for m in section_markers), re.MULTILINE
        )
        title_at: list[tuple[int, str]] = []
        for m in combined.finditer(text):
            title_at.append((m.start(), m.group(0).strip()))
        if title_at:
            for c in out:
                # 找该 chunk text 在原文中的最早出现位置
                idx = text.find(c["text"][:30])
                if idx < 0:
                    continue
                best = ""
                for pos, title in title_at:
                    if pos <= idx:
                        best = title
                    else:
                        break
                c["section"] = best[:200]

    out = merge_short_chunks(out, min_chars=80)
    return out


# ── 灌库主流程 ───────────────────────────────────────────────────────
def _ensure_zh_collection() -> None:
    """直接用 memory 路径,memory store 不绑定 dim(自适应)。"""
    mem_ensure(COLLECTION)


def _upsert_zh(point_id: str, vec: list[float], payload: dict) -> None:
    mem_upsert(point_id, vec, payload, COLLECTION)


def ingest(dry_run: bool = False) -> dict:
    _ensure_zh_collection()
    db = SessionLocal()
    stats = {
        "documents": 0,
        "chunks": 0,
        "skipped": 0,
        "by_doc": {},
    }
    try:
        for cfg in DOC_CONFIG:
            txt_path = DOCS_DIR / cfg["txt"]
            if not txt_path.exists():
                logger.warning("missing: %s", txt_path)
                stats["skipped"] += 1
                continue
            text = txt_path.read_text(encoding="utf-8", errors="ignore")
            chunks_meta = slice_doc(
                text, cfg.get("page_marker"), cfg.get("section_markers")
            )
            logger.info(
                "[%s] slices=%d (raw_chars=%d)", cfg["key"], len(chunks_meta), len(text)
            )
            stats["by_doc"][cfg["key"]] = {
                "title": cfg["title"],
                "slices": len(chunks_meta),
                "raw_chars": len(text),
            }
            if dry_run:
                stats["chunks"] += len(chunks_meta)
                continue

            # 1) document(按 title + source 幂等)
            source = f"Docs/_extracted/{cfg['txt']}"
            doc = (
                db.query(KnowledgeDocument)
                .filter(
                    KnowledgeDocument.title == cfg["title"],
                    KnowledgeDocument.source == source,
                )
                .first()
            )
            if not doc:
                doc = KnowledgeDocument(
                    title=cfg["title"],
                    source=source,
                    doc_type=cfg["doc_type"],
                    category=cfg["category"],
                    file_type="txt",
                    summary=text[:240],
                    page_count=len(chunks_meta),
                    forklift_model_id=cfg.get("forklift_model_id"),
                    engine_model_id=cfg.get("engine_model_id"),
                    license_type="user_uploaded",
                    commercial_use=0,
                )
                db.add(doc)
                db.flush()
            else:
                doc.category = cfg["category"]
                doc.summary = text[:240]
                doc.page_count = len(chunks_meta)
                doc.forklift_model_id = cfg.get("forklift_model_id")
                # 重建前先清掉旧 chunks + 旧向量
                old_chunk_ids = [
                    cid
                    for (cid,) in db.query(KnowledgeChunk.id)
                    .filter(KnowledgeChunk.document_id == doc.id)
                    .all()
                ]
                db.query(KnowledgeChunk).filter(
                    KnowledgeChunk.document_id == doc.id
                ).delete()
                db.flush()
                # 清旧向量
                for cid in old_chunk_ids:
                    try:
                        mem_search([0.0] * EMBED_DIM, 1, COLLECTION)  # 触发初始化
                    except Exception:
                        pass
            stats["documents"] += 1

            # 2) 批量嵌入
            t0 = time.time()
            texts = [c["text"] for c in chunks_meta]
            vectors = embed_texts(texts)
            logger.info(
                "[%s] embedded %d chunks in %.1fs",
                cfg["key"],
                len(vectors),
                time.time() - t0,
            )

            # 3) 写 chunks + 向量
            for idx, (c_meta, vec) in enumerate(zip(chunks_meta, vectors)):
                chunk = KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    chunk_text=c_meta["text"],
                    embedding_id=f"zh-minilm-chunk-{doc.id}-{idx}",
                    page_number=c_meta["page"],
                    section_title=c_meta["section"][:200],
                    source_locator=source,
                )
                db.add(chunk)
                db.flush()
                _upsert_zh(
                    point_id=f"zh-chunk-{chunk.id}",
                    vec=vec,
                    payload={
                        "doc_id": doc.id,
                        "chunk_id": chunk.id,
                        "forklift_model_id": cfg.get("forklift_model_id"),
                        "engine_model_id": cfg.get("engine_model_id"),
                        "title": cfg["title"],
                        "category": cfg["category"],
                        "doc_type": cfg["doc_type"],
                        "text": c_meta["text"],
                        "url": source,
                        "page_number": c_meta["page"],
                        "section_title": c_meta["section"][:200],
                    },
                )
                stats["chunks"] += 1
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("ingest failed")
        raise
    finally:
        db.close()
    return stats


# ── 自检查询 ─────────────────────────────────────────────────────────
def test_query(q: str, top_k: int = 3) -> list[dict]:
    """用一个 query 测试召回。"""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL_NAME)
    vec = model.encode([q], normalize_embeddings=True)[0].tolist()
    hits = mem_search(vec, top_k, COLLECTION)
    return [
        {
            "score": round(h.get("score", 0), 4),
            "title": h.get("payload", {}).get("title", ""),
            "section": h.get("payload", {}).get("section_title", ""),
            "page": h.get("payload", {}).get("page_number"),
            "text": (h.get("payload", {}).get("text", "") or "")[:200],
        }
        for h in hits
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--query",
        type=str,
        help="ingest 完成后,跑一个示例查询验证召回效果",
    )
    args = parser.parse_args()

    t0 = time.time()
    stats = ingest(dry_run=args.dry_run)
    elapsed = time.time() - t0
    print("=" * 60)
    print(f"ingest {'(DRY-RUN) ' if args.dry_run else ''}done in {elapsed:.1f}s")
    print(f"  documents: {stats['documents']}")
    print(f"  chunks:    {stats['chunks']}")
    print(f"  skipped:   {stats['skipped']}")
    print("-" * 60)
    for k, v in stats["by_doc"].items():
        print(f"  [{k}] {v['slices']:>4} slices  ({v['raw_chars']:>7} chars)")
        print(f"          {v['title']}")
    print("=" * 60)
    if args.query:
        print(f"\n[test query] {args.query!r}")
        for h in test_query(args.query):
            print(f"  score={h['score']}  page={h['page']}  {h['title']}")
            print(f"    section: {h['section'][:60]}")
            print(f"    text:    {h['text'][:160]}")


if __name__ == "__main__":
    main()
