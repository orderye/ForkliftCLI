"""Day 2-3: 填 ar_model_config 三行(FD30 + EFG320n + CQD20h)。

数据源(直接摘自 Docs/_extracted 的 3 份手册):
  - 龙工 FD30  / 永恒力 EFG 316n/320n / 杭叉 CQD20H

每条 AR 配置需要:
  - model_3d_id(指向 model_3d 表,本脚本顺带创建 3 条占位记录)
  - 7 个真实尺寸字段(从 PDF 摘录)
  - 比例 1:1 + 标准锚点 + 阴影/光照

执行: python3 -m scripts.import_ar_config [--dry-run]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.forklift import ForkliftModel  # noqa: E402
from app.models.model3d import Model3D, ArModelConfig  # noqa: E402


# (forklift_model_id, model_3d 名称, 真实尺寸 7 字段)
AR_CONFIGS = [
    {
        "fmid": 57,  # 龙工 FD30
        "model_name": "龙工 FD30 内燃叉车 3D 模型",
        "dim": {
            "real_length_mm": 3750.0,        # 全长
            "real_width_mm": 1225.0,         # 全宽
            "real_height_mm": 4272.0,        # 全高(货叉升起)
            "real_mast_height_mm": 4272.0,   # 门架最大高度
            "real_wheelbase_mm": 1700.0,     # 轴距
            "real_turning_radius_mm": 2460.0,  # 转弯半径(外侧)
        },
        "source": "龙工 FD30 参数表(2026-09-12 OCR 提取)",
    },
    {
        "fmid": 51,  # 永恒力 EFG316n(316n 与 320n 尺寸相同,只差载荷/自重)
        "model_name": "永恒力 EFG 316n/320n 电动叉车 3D 模型",
        "dim": {
            "real_length_mm": 3260.0,        # L1 长度(含货叉)
            "real_width_mm": 1120.0,         # b1 总宽度
            "real_height_mm": 4220.0,        # h4 提升门架升起时高度
            "real_mast_height_mm": 4220.0,   # 同上(门架全升)
            "real_wheelbase_mm": 1490.0,     # y 轮距
            "real_turning_radius_mm": 2030.0,  # Wa 转弯半径
        },
        "source": "永恒力 EFG 316n/320n 操作手册 B 章 3.1/3.2(2026-09-12 提取)",
    },
    {
        "fmid": 56,  # 杭叉 CQD20H
        "model_name": "杭叉 CQD20H 前移式叉车 3D 模型",
        "dim": {
            "real_length_mm": 1802.0,        # 长(不带货叉;含货叉再加)
            "real_width_mm": 1240.0,         # 宽
            "real_height_mm": 2070.0,        # 高(门架收缩)
            "real_mast_height_mm": 5410.0,   # 2070 + 3000 起升 + 340 自由起升 ≈ 5410
            "real_wheelbase_mm": None,       # 说明书未给(同前移式通用 ~1450)
            "real_turning_radius_mm": 1680.0,  # 最小转弯半径
        },
        "source": "杭叉 CQD12-20H 使用说明书 附表(2026-09-12 提取)",
    },
]


def _get_or_create_3d(db, name: str, fmid: int) -> Model3D:
    """幂等创建 model_3d 占位。"""
    m = db.query(Model3D).filter(Model3D.name == name).first()
    if m:
        return m
    m = Model3D(
        forklift_model_id=fmid,
        name=name,
        description="Day 2-3 自动占位;真实 GLB 待上传后替换 file_url",
        file_url=f"/uploads/models/{fmid}/placeholder.glb",
        thumbnail_url="",
        source="",
        file_size_mb=0.0,
        format="glb",
        version=1,
        status="placeholder",
        license_type="self_owned",
        commercial_use=1,
    )
    db.add(m)
    db.flush()
    return m


def _upsert_ar(db, fmid: int, model_3d_id: int, dim: dict, source: str) -> ArModelConfig:
    """幂等写入 ar_model_config(以 forklift_model_id 唯一)。"""
    cfg = (
        db.query(ArModelConfig)
        .filter(ArModelConfig.forklift_model_id == fmid)
        .first()
    )
    if not cfg:
        cfg = ArModelConfig(
            model_3d_id=model_3d_id,
            forklift_model_id=fmid,
            **dim,
            scale_factor=1.0,
            anchor_type="horizontal_plane",
            occlusion=1,
            lighting=1,
            shadow=1,
        )
        db.add(cfg)
        db.flush()
        action = "INSERT"
    else:
        # 已存在:更新尺寸(以新数据为准)
        cfg.model_3d_id = model_3d_id
        for k, v in dim.items():
            setattr(cfg, k, v)
        cfg.scale_factor = 1.0
        action = "UPDATE"
    return cfg, action


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print("=" * 60)
        print("Day 2-3: ar_model_config 灌库")
        print("=" * 60)
        for cfg in AR_CONFIGS:
            fmid = cfg["fmid"]
            m = db.query(ForkliftModel).filter(ForkliftModel.id == fmid).first()
            if not m:
                print(f"  ✗ fmid={fmid} 不存在,跳过")
                continue
            if args.dry_run:
                print(f"  DRY: fmid={fmid} ({m.name})  -> 7 字段")
                for k, v in cfg["dim"].items():
                    print(f"      {k} = {v}")
                continue
            m3d = _get_or_create_3d(db, cfg["model_name"], fmid)
            ar_cfg, action = _upsert_ar(db, fmid, m3d.id, cfg["dim"], cfg["source"])
            print(f"  [{action}] fmid={fmid} ({m.name})  model_3d_id={m3d.id}  ar_id={ar_cfg.id}")
            for k, v in cfg["dim"].items():
                if v is not None:
                    print(f"      {k} = {v}")
        if not args.dry_run:
            db.commit()
            print()
            print("=" * 60)
            print("DB 校验")
            print("=" * 60)
            rows = db.query(ArModelConfig).all()
            for r in rows:
                m = db.query(ForkliftModel).filter(ForkliftModel.id == r.forklift_model_id).first()
                mname = m.name if m else "(无)"
                print(f"  ar#{r.id}  fmid={r.forklift_model_id} ({mname})  L={r.real_length_mm}  W={r.real_width_mm}  H={r.real_height_mm}  mast={r.real_mast_height_mm}  wb={r.real_wheelbase_mm}  tr={r.real_turning_radius_mm}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
