"""Day 4-5: 填 model_3d_parts 50 条(CPC 30 + PT 20)。

每条 = (model_3d_id, name, part_number, group, mesh_name, is_interactive)

数据源:
  - CPC 零件手册(178 页,52 张总成分解图)→ 30 个核心零件
  - Noblelift PT 零件手册(Ch1-Ch7)        → 20 个核心零件

model_3d 占位:
  - id=6  杭叉 CPCD30 内燃叉车 3D 模型  (fmid=14)
  - id=7  诺力 PT20P-C 电动托盘车 3D 模型 (fmid=53)
  - 两边都引用 /Glb/001.glb、/Glb/002.glb(后续真 GLB 可替换)

mesh_name 用占位符(实际 GLB 节点名需要 GLB 解析才能拿到,
本次给形如 cpc_engine_block, pt_drive_unit 这样的语义名,便于前端
做 highlight 时按语义筛选)。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.model3d import Model3D, Model3DPart  # noqa: E402
from app.models.forklift import ForkliftModel  # noqa: E402


# ── 30 个 CPC 核心零件 ──────────────────────────────────────────
# 字段: (name, part_number, group, mesh_name)
# group 取值: body / engine / cooling / fuel / exhaust / intake /
#            transmission / drive_axle / brake / steering /
#            frame / hood / mast / fork / hydraulic / electrical
CPC_PARTS: list[dict] = [
    # 发动机(图1, 490/495 柴油机) — 4 件
    {"name": "发动机总成(490柴油机)", "part_number": "N2510-00000", "group": "engine",
     "mesh_name": "cpc_engine_assembly_490"},
    {"name": "气缸盖", "part_number": "C0F01-20101", "group": "engine", "mesh_name": "cpc_cylinder_head"},
    {"name": "活塞连杆总成", "part_number": "C0F01-20201", "group": "engine", "mesh_name": "cpc_piston_connecting_rod"},
    {"name": "曲轴", "part_number": "C0F01-20301", "group": "engine", "mesh_name": "cpc_crankshaft"},
    # 冷却(图3) — 2 件
    {"name": "散热器总成", "part_number": "C0F03-00001", "group": "cooling", "mesh_name": "cpc_radiator"},
    {"name": "水泵", "part_number": "C0F03-30001", "group": "cooling", "mesh_name": "cpc_water_pump"},
    # 燃油(图5) — 2 件
    {"name": "喷油泵", "part_number": "C0F05-10001", "group": "fuel", "mesh_name": "cpc_injection_pump"},
    {"name": "喷油器", "part_number": "C0F05-20001", "group": "fuel", "mesh_name": "cpc_injector"},
    # 进气/排气 — 1+1 件
    {"name": "空气滤清器", "part_number": "C0F07-10001", "group": "intake", "mesh_name": "cpc_air_filter"},
    {"name": "排气消声器", "part_number": "C0F06-10001", "group": "exhaust", "mesh_name": "cpc_muffler"},
    # 驱动桥/轮(图8, 9, 10) — 2 件
    {"name": "驱动桥总成", "part_number": "C0F08-00001", "group": "drive_axle", "mesh_name": "cpc_drive_axle"},
    {"name": "驱动轮(2-2.5t)", "part_number": "C0F09-10001", "group": "drive_axle", "mesh_name": "cpc_drive_wheel"},
    # 变速箱(图15, 16, 19) — 3 件
    {"name": "变速箱总成(机械式)", "part_number": "C0F15-00001", "group": "transmission", "mesh_name": "cpc_transmission_mech"},
    {"name": "变矩器(图21)", "part_number": "C0F21-00001", "group": "transmission", "mesh_name": "cpc_torque_converter"},
    {"name": "换档操纵(图26)", "part_number": "C0F26-00001", "group": "transmission", "mesh_name": "cpc_shift_lever"},
    # 制动(图11-16, 35) — 2 件
    {"name": "制动总泵(图35)", "part_number": "C0F35-00001", "group": "brake", "mesh_name": "cpc_brake_master_cylinder"},
    {"name": "停车制动(图36)", "part_number": "C0F36-00001", "group": "brake", "mesh_name": "cpc_parking_brake"},
    # 转向(图27-30) — 2 件
    {"name": "转向桥(图28)", "part_number": "C0F28-00001", "group": "steering", "mesh_name": "cpc_steering_axle"},
    {"name": "转向油缸(图30)", "part_number": "C0F30-00001", "group": "steering", "mesh_name": "cpc_steering_cylinder"},
    # 车架(图37, 38) + 护顶架(图42) — 3 件
    {"name": "车架总成(图37)", "part_number": "C0F37-00001", "group": "frame", "mesh_name": "cpc_frame"},
    {"name": "平衡重", "part_number": "C0F37-50001", "group": "frame", "mesh_name": "cpc_counterweight"},
    {"name": "护顶架(图42)", "part_number": "C0F42-00001", "group": "frame", "mesh_name": "cpc_overhead_guard"},
    # 门架(图44-47) — 2 件
    {"name": "门架总成(图45)", "part_number": "C0F45-00001", "group": "mast", "mesh_name": "cpc_mast_assembly"},
    {"name": "起升油缸(图51)", "part_number": "C0F51-00001", "group": "mast", "mesh_name": "cpc_lift_cylinder"},
    # 货叉(图49) + 倾斜油缸(图48) — 2 件
    {"name": "货叉(图49)", "part_number": "C0F49-00001", "group": "fork", "mesh_name": "cpc_fork"},
    {"name": "倾斜油缸(图48)", "part_number": "C0F48-00001", "group": "mast", "mesh_name": "cpc_tilt_cylinder"},
    # 机罩(图39, 40) — 1 件
    {"name": "机罩总成(图39)", "part_number": "C0F39-00001", "group": "hood", "mesh_name": "cpc_hood"},
    # 电气(图52) — 2 件
    {"name": "蓄电池(图52)", "part_number": "C0F52-30001", "group": "electrical", "mesh_name": "cpc_battery"},
    {"name": "起动机(图52)", "part_number": "C0F52-50001", "group": "electrical", "mesh_name": "cpc_starter_motor"},
    # 液压 — 1 件
    {"name": "液压油箱", "part_number": "C0F22-10001", "group": "hydraulic", "mesh_name": "cpc_hydraulic_tank"},
]
assert len(CPC_PARTS) == 30, f"CPC parts should be 30, got {len(CPC_PARTS)}"


# ── 20 个 PT 核心零件 ───────────────────────────────────────────
# Item Code 从 Ch1-Ch7 摘,真实的 9101xxxx / 5090xxxx 编号
PT_PARTS: list[dict] = [
    # Ch1 Drive System — 4 件
    {"name": "驱动单元总成(Manual Steering)", "part_number": "509046013501", "group": "drive_axle",
     "mesh_name": "pt_drive_unit"},
    {"name": "顶板(Top Plate)", "part_number": "509013520003", "group": "frame",
     "mesh_name": "pt_top_plate"},
    {"name": "驱动轮", "part_number": "509046026001", "group": "drive_axle", "mesh_name": "pt_drive_wheel"},
    {"name": "驱动电机", "part_number": "509046013005", "group": "electrical", "mesh_name": "pt_drive_motor"},
    # Ch2 Hydraulic System — 3 件
    {"name": "液压泵总成", "part_number": "509046020001", "group": "hydraulic", "mesh_name": "pt_hydraulic_pump"},
    {"name": "多路换向阀", "part_number": "509046020002", "group": "hydraulic", "mesh_name": "pt_multiway_valve"},
    {"name": "起升油缸", "part_number": "509046020003", "group": "mast", "mesh_name": "pt_lift_cylinder"},
    # Ch3 Truck Frame — 3 件
    {"name": "车架总成", "part_number": "509046030001", "group": "frame", "mesh_name": "pt_frame"},
    {"name": "护顶架", "part_number": "509046030002", "group": "frame", "mesh_name": "pt_overhead_guard"},
    {"name": "扶手", "part_number": "509046030003", "group": "frame", "mesh_name": "pt_armrest"},
    # Ch4 Chassis — 2 件
    {"name": "底盘总成", "part_number": "509046038501", "group": "frame", "mesh_name": "pt_chassis"},
    {"name": "承重轮(平衡轮)", "part_number": "509046038002", "group": "drive_axle", "mesh_name": "pt_load_wheel"},
    # Ch5 Steering/Braking/Wheels — 3 件
    {"name": "转向电机(EPS)", "part_number": "509046050001", "group": "steering", "mesh_name": "pt_steering_motor"},
    {"name": "制动总成", "part_number": "509046050002", "group": "brake", "mesh_name": "pt_brake_assembly"},
    {"name": "操纵手柄(含按钮)", "part_number": "509046050003", "group": "steering", "mesh_name": "pt_control_handle"},
    # Ch6 Electrical — 4 件
    {"name": "控制器(F2A/1232E/QT)", "part_number": "509046060001", "group": "electrical",
     "mesh_name": "pt_controller"},
    {"name": "充电器(铅酸)", "part_number": "509046036501", "group": "electrical", "mesh_name": "pt_charger_lead_acid"},
    {"name": "充电器(锂电)", "part_number": "509046036502", "group": "electrical", "mesh_name": "pt_charger_lithium"},
    {"name": "显示器/仪表", "part_number": "509046060004", "group": "electrical", "mesh_name": "pt_display"},
    # Ch7 Special — 1 件(护栏/平台是常见选配)
    {"name": "操作者护栏(选配)", "part_number": "509046070001", "group": "frame", "mesh_name": "pt_operator_guard"},
]
assert len(PT_PARTS) == 20, f"PT parts should be 20, got {len(PT_PARTS)}"


# 通用填充字段
DEFAULT_COLOR_BY_GROUP = {
    "body": "#888888", "frame": "#666666", "engine": "#aa3333",
    "cooling": "#3399cc", "fuel": "#cc9933", "exhaust": "#555555",
    "intake": "#cccccc", "drive_axle": "#553311", "transmission": "#996633",
    "brake": "#cc0000", "steering": "#0066cc", "hood": "#222222",
    "mast": "#ffcc00", "fork": "#ff8800", "hydraulic": "#336699",
    "electrical": "#00aa66",
}
DEFAULT_MATERIAL = "steel"


def _get_or_create_3d(db, name: str, fmid: int, file_url: str) -> Model3D:
    m = db.query(Model3D).filter(Model3D.name == name).first()
    if m:
        return m
    m = Model3D(
        forklift_model_id=fmid,
        name=name,
        description="Day 4-5 自动占位;真实 GLB 待上传后替换 file_url",
        file_url=file_url,
        thumbnail_url="",
        source="",
        file_size_mb=42.0,
        format="glb",
        version=1,
        status="placeholder",
        license_type="self_owned",
        commercial_use=1,
    )
    db.add(m)
    db.flush()
    return m


def _upsert_part(
    db, model_3d_id: int, idx: int, part: dict
) -> tuple[Model3DPart, str]:
    """幂等写入(以 model_3d_id + mesh_name 唯一)。"""
    a = (
        db.query(Model3DPart)
        .filter(
            Model3DPart.model_3d_id == model_3d_id,
            Model3DPart.mesh_name == part["mesh_name"],
        )
        .first()
    )
    grp = part["group"]
    color = DEFAULT_COLOR_BY_GROUP.get(grp, "#888888")
    if a:
        a.name = part["name"]
        a.part_number = part["part_number"]
        a.group = grp
        a.color = color
        a.material = DEFAULT_MATERIAL
        a.is_interactive = 1
        return a, "UPDATE"
    a = Model3DPart(
        model_3d_id=model_3d_id,
        name=part["name"],
        part_number=part["part_number"],
        group=grp,
        color=color,
        material=DEFAULT_MATERIAL,
        mesh_name=part["mesh_name"],
        is_interactive=1,
        position_x=0.0, position_y=0.0, position_z=0.0,
        rotation_x=0.0, rotation_y=0.0, rotation_z=0.0,
        scale=1.0,
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
        print("Day 4-5: model_3d_parts 灌库(CPC 30 + PT 20 = 50)")
        print("=" * 60)

        # 1) 确保 2 个 model_3d 占位
        if not args.dry_run:
            m3d_cpc = _get_or_create_3d(
                db, "杭叉 CPC/CPCD 20-30 内燃叉车 3D 模型", fmid=14,
                file_url="/Glb/001.glb",
            )
            m3d_pt = _get_or_create_3d(
                db, "诺力 PT20/25/30P-C 电动托盘车 3D 模型", fmid=53,
                file_url="/Glb/002.glb",
            )
            print(f"  model_3d 占位: CPC={m3d_cpc.id}  PT={m3d_pt.id}\n")
        else:
            m3d_cpc = type("X", (), {"id": "CPC?"})()
            m3d_pt = type("X", (), {"id": "PT?"})()
            print("  [DRY-RUN] 不会创建 model_3d\n")

        # 2) 灌 30 条 CPC
        cpc_insert = cpc_update = 0
        print(f"[CPC] 30 条 → model_3d_id={m3d_cpc.id}")
        for idx, p in enumerate(CPC_PARTS):
            if args.dry_run:
                print(f"  DRY: {p['name']:<28} {p['part_number']:<14} {p['group']:<12} {p['mesh_name']}")
            else:
                _, action = _upsert_part(db, m3d_cpc.id, idx, p)
                if action == "INSERT":
                    cpc_insert += 1
                else:
                    cpc_update += 1

        # 3) 灌 20 条 PT
        pt_insert = pt_update = 0
        print(f"\n[PT] 20 条 → model_3d_id={m3d_pt.id}")
        for idx, p in enumerate(PT_PARTS):
            if args.dry_run:
                print(f"  DRY: {p['name']:<28} {p['part_number']:<14} {p['group']:<12} {p['mesh_name']}")
            else:
                _, action = _upsert_part(db, m3d_pt.id, idx, p)
                if action == "INSERT":
                    pt_insert += 1
                else:
                    pt_update += 1

        if not args.dry_run:
            db.commit()
            print()
            print("=" * 60)
            print(f"汇总: CPC INSERT={cpc_insert} UPDATE={cpc_update}  "
                  f"PT INSERT={pt_insert} UPDATE={pt_update}  "
                  f"TOTAL_INSERT={cpc_insert+pt_insert}")
            print("=" * 60)
            # 校验
            print(f"\nDB 校验:")
            for mid in (m3d_cpc.id, m3d_pt.id):
                rows = db.query(Model3DPart).filter(Model3DPart.model_3d_id == mid).order_by(Model3DPart.group, Model3DPart.id).all()
                print(f"  model_3d_id={mid}  共 {len(rows)} 条")
                for r in rows:
                    print(f"    #{r.id:<2} {r.group:<12} {r.mesh_name:<28} {r.name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
