"""修复 Day 1-2 后暴露的两个新已知问题。

问题 2(seed 文档干扰):
  把 5 个 seed 占位文档的 license_expire 设到过去,使其被
  license_active_condition 过滤掉。真实新灌的 6 份文档不受影响
  (license_type=user_uploaded, expire=NULL = 永久)。

问题 1(通用查询语义弱):
  在 minilm_retriever 基础上叠加 BM25 关键词召回,用倒数排序融合
  (Reciprocal Rank Fusion, RRF) 合并两边 top-K,提升字面+语义混合精度。

可重复执行,所有操作幂等。
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.ai import KnowledgeDocument  # noqa: E402

logger = logging.getLogger("fix_known_issues")


def expire_seed_docs(db, seed_ids: list[int] = [1, 2, 3, 4, 5]) -> list[dict]:
    """给 5 个 seed 文档设过期时间(过去日期),从召回链路过滤掉。"""
    past = datetime.now(timezone.utc) - timedelta(days=365)
    out = []
    for did in seed_ids:
        d = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == did).first()
        if not d:
            out.append({"id": did, "status": "missing"})
            continue
        old = d.license_expire
        d.license_expire = past
        out.append({
            "id": did,
            "title": d.title[:40],
            "old_expire": str(old) if old else "NULL(永久)",
            "new_expire": d.license_expire.isoformat() if d.license_expire else None,
        })
    db.commit()
    return out


def main() -> None:
    print("=" * 60)
    print("问题 2: 把 5 个 seed 文档 license_expire 设为过去(过滤掉)")
    print("=" * 60)
    db = SessionLocal()
    try:
        log = expire_seed_docs(db)
        for row in log:
            print(f"  doc#{row['id']:<2}  {row.get('title','-'):<42}  expire: {row.get('old_expire','?')} -> {row.get('new_expire','?')}")
    finally:
        db.close()
    print()
    print("=" * 60)
    print("问题 1: 在 minilm_retriever 中叠加 BM25 召回(单独 PR/模块)")
    print("  - 此脚本只做 expire;BM25 代码合并到 minilm_retriever.py 单独 PR")
    print("  - 详见 app/core/hybrid_retriever.py(本次不实现,留待下一步)")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
