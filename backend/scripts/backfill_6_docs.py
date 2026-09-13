"""回填 6 份新灌知识库的车型关联 + 补齐缺失的 brands/series/models。

策略(幂等):
  - 缺失的 brand(永恒力/Jungheinrich, Noblelift) → 增
  - 缺失的 series(杭叉 CQD 前移式, 龙工 FD, 永恒力 EFG, Noblelift PT) → 增
  - 缺失的 model(CQD20H, FD30, EFG316n, EFG320n, PT20P-C/25P-C/30P-C) → 增
  - 6 份 doc 的 forklift_model_id 按下表回填
  - 通用文档(液压)保持 NULL
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.forklift import ForkliftBrand, ForkliftSeries, ForkliftModel  # noqa: E402
from app.models.ai import KnowledgeDocument  # noqa: E402


# 计划新增的(brand / series / model)
PLAN = [
    # 永恒力(中文品牌)
    {
        "brand": ("永恒力", "Jungheinrich", "德国"),
        "series": ("EFG", "电动平衡重叉车,1.6-2.0t"),
        "models": [
            ("EFG316n", 1600, 3000, "electric"),
            ("EFG320n", 2000, 3000, "electric"),
        ],
    },
    # Noblelift(中文"诺力"在国内市场较通用)
    {
        "brand": ("诺力", "Noblelift", "中国"),
        "series": ("PT系列", "电动托盘搬运车,步行式,2-3t"),
        "models": [
            ("PT20P-C", 2000, None, "electric"),
            ("PT25P-C", 2500, None, "electric"),
            ("PT30P-C", 3000, None, "electric"),
        ],
    },
    # 杭叉(品牌已存在,只加新 series + model)
    {
        "brand": ("杭叉", "Hangcha", "中国"),  # 已存在,会幂等跳过
        "series": ("CQD前移式", "电动前移式叉车,1.2-2.0t"),
        "models": [
            ("CQD20H", 2000, None, "electric"),
        ],
    },
    # 龙工(品牌已存在,只加新 series + model)
    {
        "brand": ("龙工", "Lonking", "中国"),  # 已存在
        "series": ("FD系列", "内燃平衡重叉车,柴油"),
        "models": [
            ("FD30", 3000, 3000, "diesel"),
        ],
    },
]

# 6 份 doc 的回填计划
DOC_BACKFILL = [
    {"title": "CPC/CPCD 20-30 内燃平衡重叉车零件手册", "fmid": 14, "note": "代表杭叉 CPCD30;覆盖全 CPCD 20-30 系列"},
    {"title": "Noblelift PT20/25/30P-C 电动托盘搬运车零件手册", "fmid": "PT20P-C", "note": "诺力 PT20P-C;整本涵盖 20/25/30 三个吨位"},
    {"title": "永恒力 EFG 316n/320n 电动叉车操作手册", "fmid": "EFG316n", "note": "主代表 316n,320n 通用"},
    {"title": "杭叉 CQD12-20H 前移式叉车使用说明书", "fmid": "CQD20H", "note": "代表 CQD20H,全系列适用"},
    {"title": "龙工 FD30 内燃平衡重叉车参数表", "fmid": "FD30", "note": "FD30"},
    {"title": "龙工叉车液压系统工作原理、常见故障与维修保养", "fmid": None, "note": "通用知识,跨品牌"},
]


def _get_or_create_brand(db, name, name_en, country) -> ForkliftBrand:
    b = db.query(ForkliftBrand).filter(ForkliftBrand.name == name).first()
    if b:
        return b
    b = ForkliftBrand(name=name, name_en=name_en, country=country)
    db.add(b)
    db.flush()
    return b


def _get_or_create_series(db, brand_id, name, description) -> ForkliftSeries:
    s = (
        db.query(ForkliftSeries)
        .filter(ForkliftSeries.brand_id == brand_id, ForkliftSeries.name == name)
        .first()
    )
    if s:
        return s
    s = ForkliftSeries(brand_id=brand_id, name=name, description=description)
    db.add(s)
    db.flush()
    return s


def _get_or_create_model(db, series_id, name, load_capacity_kg, lift_height_mm, fuel_type) -> ForkliftModel:
    m = (
        db.query(ForkliftModel)
        .filter(ForkliftModel.series_id == series_id, ForkliftModel.name == name)
        .first()
    )
    if m:
        return m
    m = ForkliftModel(
        series_id=series_id,
        name=name,
        load_capacity_kg=load_capacity_kg,
        load_capacity_ton=(load_capacity_kg / 1000) if load_capacity_kg else None,
        lift_height_mm=lift_height_mm,
        fuel_type=fuel_type,
    )
    db.add(m)
    db.flush()
    return m


def seed_models(db) -> dict:
    """按 PLAN 幂等创建/补全品牌/系列/车型。返回 {model_name: id}。"""
    out: dict[str, int] = {}
    for entry in PLAN:
        name, name_en, country = entry["brand"]
        brand = _get_or_create_brand(db, name, name_en, country)
        s_name, s_desc = entry["series"]
        series = _get_or_create_series(db, brand.id, s_name, s_desc)
        for m_name, load_kg, lift_mm, fuel in entry["models"]:
            m = _get_or_create_model(db, series.id, m_name, load_kg, lift_mm, fuel)
            out[m_name] = m.id
    db.commit()
    return out


def backfill_docs(db, name_to_id: dict) -> list[dict]:
    """按 DOC_BACKFILL 回填 6 份 doc 的 forklift_model_id。"""
    log = []
    for entry in DOC_BACKFILL:
        doc = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.title == entry["title"])
            .first()
        )
        if not doc:
            log.append({"title": entry["title"], "status": "missing-doc"})
            continue
        target = entry["fmid"]
        if isinstance(target, str):
            new_id = name_to_id.get(target)
        else:
            new_id = target
        old_id = doc.forklift_model_id
        if new_id != old_id:
            doc.forklift_model_id = new_id
            log.append({
                "title": entry["title"],
                "old": old_id,
                "new": new_id,
                "note": entry["note"],
            })
        else:
            log.append({
                "title": entry["title"],
                "old": old_id,
                "new": new_id,
                "note": "unchanged",
            })
    db.commit()
    return log


def main() -> None:
    db = SessionLocal()
    try:
        print("=" * 60)
        print("Step 1: 创建/补全品牌/系列/车型")
        print("=" * 60)
        name_to_id = seed_models(db)
        for n, i in name_to_id.items():
            print(f"  model {n:<12} -> id={i}")
        print()
        print("=" * 60)
        print("Step 2: 回填 6 份 doc 的 forklift_model_id")
        print("=" * 60)
        log = backfill_docs(db, name_to_id)
        for row in log:
            print(f"  {row.get('title','?')[:40]:<42}  old={row.get('old')}  new={row.get('new')}  {row.get('note','')}")
        print()
        print("=" * 60)
        print("Step 3: 校验")
        print("=" * 60)
        rows = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.id >= 6)
            .all()
        )
        for d in rows:
            mid = d.forklift_model_id
            mname = ""
            if mid:
                m = db.query(ForkliftModel).filter(ForkliftModel.id == mid).first()
                if m:
                    mname = m.name
            print(f"  doc#{d.id:<2} {d.title[:38]:<40}  fmid={mid}  ({mname})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
