#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def safe_name(name: str) -> str:
    name = os.path.basename(name.strip())
    if not name or name in {'.', '..'} or '/' in name or '\\' in name:
        raise ValueError('bad filename')
    return name


def build_template() -> dict:
    return {
        "name": "Forklift",
        "format": "fbx",
        "scale_unit": "meters",
        "created_at": datetime.now().isoformat(),
        "source_file": "Forklift.STEP",
        "export_date": datetime.now().strftime("%Y-%m-%d"),
        "parts": [
            {"mesh_name": "Body_Chassis", "part_id": 1, "name": "车身底盘", "group": "body", "is_interactive": False, "is_static": True},
            {"mesh_name": "Mast_Outer", "part_id": 2, "name": "外门架", "group": "mast", "is_interactive": False, "is_static": True},
            {"mesh_name": "Mast_Inner", "part_id": 3, "name": "内门架", "group": "mast", "is_interactive": True, "is_static": False, "parent_part": 2, "animation_type": "lift", "min_value": 1800, "max_value": 4500, "unit": "mm"},
            {"mesh_name": "Carriage_Fork", "part_id": 4, "name": "货叉架", "group": "fork", "is_interactive": True, "is_static": False, "parent_part": 3, "animation_type": "lift_child"},
            {"mesh_name": "Fork_Left", "part_id": 5, "name": "左货叉", "group": "fork", "is_interactive": True, "is_static": False, "parent_part": 4, "animation_type": "slide"},
            {"mesh_name": "Fork_Right", "part_id": 6, "name": "右货叉", "group": "fork", "is_interactive": True, "is_static": False, "parent_part": 4, "animation_type": "slide"},
            {"mesh_name": "Counterweight", "part_id": 7, "name": "配重", "group": "body", "is_interactive": False, "is_static": True},
            {"mesh_name": "Cabin", "part_id": 8, "name": "驾驶室", "group": "body", "is_interactive": False, "is_static": True}
        ],
        "animations": [
            {"name": "mast_lift", "display_name": "门架升降", "type": "linear", "duration_ms": 3000, "loop": False, "affected_parts": [3, 4, 5, 6], "control_method": "slider"},
            {"name": "mast_tilt", "display_name": "门架倾斜", "type": "rotation", "duration_ms": 2000, "loop": False, "affected_parts": [2, 3, 4, 5, 6], "control_method": "buttons", "axis": "x", "min_angle": -12, "max_angle": 6},
            {"name": "fork_spread", "display_name": "货叉开合", "type": "slide", "duration_ms": 1500, "loop": False, "affected_parts": [5, 6], "control_method": "buttons"}
        ],
        "ar_config": {
            "real_length_mm": 3450,
            "real_width_mm": 1200,
            "real_height_mm": 2100,
            "real_mast_height_mm": 4500,
            "real_wheelbase_mm": 1650,
            "real_turning_radius_mm": 2500,
            "real_weight_kg": 3800,
            "real_load_capacity_kg": 3000
        },
        "physics": {"center_of_mass": [0, 1.0, 0], "mass_kg": 3800}
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', default='.')
    p.add_argument('--name', default='forklift_metadata.json')
    args = p.parse_args()

    outdir = Path(args.output).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / safe_name(args.name)
    data = build_template()
    outfile.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(outfile)


if __name__ == '__main__':
    main()
