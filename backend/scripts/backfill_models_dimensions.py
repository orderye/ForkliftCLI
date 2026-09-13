"""回填 3 个新车型的 forkift_models 尺寸字段(length/width/height/wheelbase/turning/lift_height)。

数据源同 ar_model_config:从手册 OCR 摘录的真实尺寸。
不与 ar_model_config 重复,只是把同一份尺寸镜像到 forklift_models,
让品牌详情页/搜索能直接看到。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.forklift import ForkliftModel  # noqa: E402


BACKFILL = [
    {
        "fmid": 57,  # 龙工 FD30
        "length_mm": 3750.0, "width_mm": 1225.0, "height_mm": 4272.0,
        "wheelbase_mm": 1700.0, "turning_radius_mm": 2460.0,
        "lift_height_mm": 3000.0, "weight_kg": 4360.0,
        "max_speed_kmh": 19.0,  # 液力式空载
    },
    {
        "fmid": 51,  # 永恒力 EFG316n
        "length_mm": 3260.0, "width_mm": 1120.0, "height_mm": 4220.0,
        "wheelbase_mm": 1490.0, "turning_radius_mm": 2030.0,
        "lift_height_mm": 3000.0, "weight_kg": 3025.0,
        "max_speed_kmh": 17.0,  # 满载
    },
    {
        "fmid": 56,  # 杭叉 CQD20H
        "length_mm": 1802.0, "width_mm": 1240.0, "height_mm": 2070.0,
        "wheelbase_mm": None, "turning_radius_mm": 1680.0,
        "lift_height_mm": 3000.0, "weight_kg": 2980.0,
        "max_speed_kmh": 10.2,  # 空载最大运行速度
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        for cfg in BACKFILL:
            m = db.query(ForkliftModel).filter(ForkliftModel.id == cfg["fmid"]).first()
            if not m:
                print(f"  ✗ fmid={cfg['fmid']} 不存在,跳过")
                continue
            changed = []
            for k, v in cfg.items():
                if k == "fmid":
                    continue
                if v is None:
                    continue
                old = getattr(m, k)
                if old != v:
                    setattr(m, k, v)
                    changed.append(f"{k}: {old} -> {v}")
            action = "UPDATE" if changed else "noop"
            print(f"  [{action}] fmid={cfg['fmid']} ({m.name})")
            for c in changed:
                print(f"      {c}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
