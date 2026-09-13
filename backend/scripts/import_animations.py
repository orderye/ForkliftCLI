"""Day 3-4: 填 model_3d_animations 24 条(3 个 model_3d × 8 个动作)。

每行 = (model_3d_id, name, display_name, animation_clip, duration_ms, loop)

参数推导(从手册 OCR 数据):
  - mast_up / mast_down:  duration = max_lift_mm / lift_speed_mm_s
  - fork_up / fork_down:   duration = 同上(同步)
  - tilt_forward / back:   duration = 1500-2000ms(典型,2°/4°/6°/12° 角度差异体现在 animation_clip 参数而非时长)
  - steer_left / right:    duration = 1000ms
  - 转向角度: arcsin(wheelbase_mm / turning_radius_mm) — Ackermann 近似,给出动画终止角度

数据源:
  FD30   - 龙工FD30参数.txt + EFG/CQD 手册对照
  EFG316n - 永恒力 B 章 3.1 性能参数
  CQD20H  - 杭叉前移式 附表(注:CQD 升降速度 "260 km/h" 系 OCR 误识别,实际为 260 mm/s)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.model3d import Model3D, Model3DAnimation  # noqa: E402
from app.models.forklift import ForkliftModel  # noqa: E402


# 三个模型的物理参数(从手册 OCR)
SPECS = {
    3: {  # model_3d_id=3 (FD30)
        "name": "龙工 FD30",
        "max_lift_mm": 3000,
        "lift_speed_mm_s": 430,        # 满载起升 430 mm/s(液力)
        "tilt_forward_deg": 6,         # 门架前倾角
        "tilt_back_deg": 12,           # 门架后倾角
        "wheelbase_mm": 1700,
        "turning_radius_mm": 2460,
    },
    4: {  # model_3d_id=4 (EFG316n/320n)
        "name": "永恒力 EFG 316n/320n",
        "max_lift_mm": 3000,
        "lift_speed_mm_s": 390,        # 320n 满载 0.39 m/s → 390 mm/s
        "tilt_forward_deg": 3,         # 电动平衡重叉车常见前倾 3°
        "tilt_back_deg": 6,            # 后倾 6°
        "wheelbase_mm": 1490,
        "turning_radius_mm": 2030,
    },
    5: {  # model_3d_id=5 (CQD20H)
        "name": "杭叉 CQD20H",
        "max_lift_mm": 3000,
        "lift_speed_mm_s": 260,        # OCR 误为 km/h,实际 260 mm/s
        "tilt_forward_deg": 2,         # 前移式前后倾角小
        "tilt_back_deg": 4,
        "wheelbase_mm": 1450,          # 说明书未给,取行业典型值
        "turning_radius_mm": 1680,
    },
}


def _compute_animations(model_3d_id: int, spec: dict) -> list[dict]:
    """根据物理参数推 8 条动画。"""
    s = spec
    mast_ms = round(s["max_lift_mm"] / s["lift_speed_mm_s"] * 1000)
    # Ackermann 转向角近似: δ = arcsin(wheelbase / turning_radius)
    steer_deg = round(math.degrees(math.asin(s["wheelbase_mm"] / s["turning_radius_mm"])), 1)
    # 倾缸动作:典型 1.5-2s,角度小则快
    tilt_ms = 1800 if s["tilt_forward_deg"] <= 3 else 2200
    steer_ms = 1000

    return [
        # 门架升降
        {
            "name": "mast_up",
            "display_name": "门架上升",
            "animation_clip": f"mast_up_{s['max_lift_mm']}mm",
            "duration_ms": mast_ms,
            "loop": 0,
            "note": f"满载起升 {s['lift_speed_mm_s']} mm/s × 3000mm",
        },
        {
            "name": "mast_down",
            "display_name": "门架下降",
            "animation_clip": f"mast_down_{s['max_lift_mm']}mm",
            "duration_ms": mast_ms,
            "loop": 0,
            "note": "下降一般略快于起升,此处同速",
        },
        # 货叉升降(与门架同步)
        {
            "name": "fork_up",
            "display_name": "货叉上升",
            "animation_clip": f"fork_up_{s['max_lift_mm']}mm",
            "duration_ms": mast_ms,
            "loop": 0,
            "note": "与门架上升同步",
        },
        {
            "name": "fork_down",
            "display_name": "货叉下降",
            "animation_clip": f"fork_down_{s['max_lift_mm']}mm",
            "duration_ms": mast_ms,
            "loop": 0,
            "note": "与门架下降同步",
        },
        # 门架倾斜
        {
            "name": "tilt_forward",
            "display_name": "门架前倾",
            "animation_clip": f"tilt_forward_{s['tilt_forward_deg']}deg",
            "duration_ms": tilt_ms,
            "loop": 0,
            "note": f"前倾 {s['tilt_forward_deg']}°",
        },
        {
            "name": "tilt_back",
            "display_name": "门架后倾",
            "animation_clip": f"tilt_back_{s['tilt_back_deg']}deg",
            "duration_ms": tilt_ms,
            "loop": 0,
            "note": f"后倾 {s['tilt_back_deg']}°",
        },
        # 转向
        {
            "name": "steer_left",
            "display_name": "左转向",
            "animation_clip": f"steer_left_{steer_deg}deg",
            "duration_ms": steer_ms,
            "loop": 0,
            "note": f"max 转向角 {steer_deg}° (Ackermann)",
        },
        {
            "name": "steer_right",
            "display_name": "右转向",
            "animation_clip": f"steer_right_{steer_deg}deg",
            "duration_ms": steer_ms,
            "loop": 0,
            "note": f"max 转向角 {steer_deg}° (Ackermann)",
        },
    ]


def _upsert_animation(db, model_3d_id: int, idx: int, anim: dict) -> tuple[Model3DAnimation, str]:
    """幂等写入(以 model_3d_id + name 唯一)。"""
    a = (
        db.query(Model3DAnimation)
        .filter(
            Model3DAnimation.model_3d_id == model_3d_id,
            Model3DAnimation.name == anim["name"],
        )
        .first()
    )
    if a:
        a.display_name = anim["display_name"]
        a.animation_clip = anim["animation_clip"]
        a.duration_ms = anim["duration_ms"]
        a.loop = anim["loop"]
        return a, "UPDATE"
    a = Model3DAnimation(
        model_3d_id=model_3d_id,
        name=anim["name"],
        display_name=anim["display_name"],
        animation_clip=anim["animation_clip"],
        duration_ms=anim["duration_ms"],
        loop=anim["loop"],
    )
    db.add(a)
    db.flush()
    return a, "INSERT"


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print("=" * 60)
        print("Day 3-4: model_3d_animations 灌库(3 模型 × 8 动作 = 24 条)")
        print("=" * 60)
        total_insert = 0
        total_update = 0
        for model_3d_id, spec in SPECS.items():
            m3d = db.query(Model3D).filter(Model3D.id == model_3d_id).first()
            if not m3d:
                print(f"  ✗ model_3d_id={model_3d_id} 不存在,跳过")
                continue
            print(f"\n[{spec['name']}] model_3d_id={model_3d_id}  "
                  f"lift={spec['lift_speed_mm_s']}mm/s  "
                  f"tilt={spec['tilt_forward_deg']}°/{spec['tilt_back_deg']}°  "
                  f"wb={spec['wheelbase_mm']}mm  tr={spec['turning_radius_mm']}mm")
            anims = _compute_animations(model_3d_id, spec)
            for idx, anim in enumerate(anims):
                if args.dry_run:
                    print(f"  DRY: {anim['name']:<15} {anim['display_name']:<8} "
                          f"{anim['duration_ms']:>5}ms  {anim['animation_clip']}")
                else:
                    _, action = _upsert_animation(db, model_3d_id, idx, anim)
                    if action == "INSERT":
                        total_insert += 1
                    else:
                        total_update += 1
                    print(f"  [{action}] {anim['name']:<15} {anim['display_name']:<8} "
                          f"{anim['duration_ms']:>5}ms  {anim['animation_clip']}")
        if not args.dry_run:
            db.commit()
            print()
            print("=" * 60)
            print(f"汇总: INSERT={total_insert}  UPDATE={total_update}  TOTAL=24")
            print("=" * 60)
            rows = db.query(Model3DAnimation).order_by(Model3DAnimation.model_3d_id, Model3DAnimation.name).all()
            print(f"\nDB 校验({len(rows)} 条):")
            for r in rows:
                print(f"  #{r.id:<2}  m3d={r.model_3d_id}  {r.name:<14} "
                      f"{r.display_name:<8} {r.duration_ms:>5}ms  loop={r.loop}  clip={r.animation_clip}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
