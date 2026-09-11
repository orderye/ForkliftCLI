"""故障树数据导入脚本"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal
from app.models.ai import FaultCode, FaultTree
from app.models.forklift import ForkliftModel
from app.models.engine import EngineModel
from sqlalchemy import select


def build_fault_trees(db: SessionLocal):
    """构建示例故障树"""
    # 先获取测试数据所需的基础实体
    stmt = select(ForkliftModel).filter(ForkliftModel.id == 1)
    forklift_model = db.execute(stmt).scalar_one_or_none()
    stmt = select(EngineModel).filter(EngineModel.id == 1)
    engine_model = db.execute(stmt).scalar_one_or_none()

    if not forklift_model:
        raise ValueError("未找到叉车型号 ID=1")
    if not engine_model:
        raise ValueError("未找到发动机型号 ID=1")

    # 获取或创建故障代码
    fault_codes = {}
    for code_data in [
        {"code": "E001", "description": "发动机启动失败", "severity": "high", "category": "engine"},
        {"code": "E002", "description": "液压系统压力低", "severity": "medium", "category": "hydraulic"},
        {"code": "E003", "description": "电气系统短路", "severity": "critical", "category": "electrical"},
        {"code": "E004", "description": "制动系统磨损", "severity": "low", "category": "brake"},
        {"code": "E005", "description": "转向系统松动", "severity": "medium", "category": "steering"},
    ]:
        stmt = select(FaultCode).filter(FaultCode.code == code_data["code"])
        fc = db.execute(stmt).scalar_one_or_none()
        if not fc:
            fc = FaultCode(
                code=code_data["code"],
                description=code_data["description"],
                severity=code_data["severity"],
                category=code_data["category"]
            )
            db.add(fc)
            db.flush()
        fault_codes[code_data["code"]] = fc

    db.commit()

    # 构建故障树数据（症状 + 原因列表 + 解决方案列表 + 概率）
    trees_data = [
        {
            "fault_code_id": fault_codes["E001"].id,
            "forklift_model_id": forklift_model.id,
            "engine_model_id": engine_model.id,
            "symptom": "发动机无法启动，仪表盘无任何指示灯亮起",
            "causes_json": [fault_codes["E001"].id],
            "solutions_json": [
                "检查电源是否接通",
                "检查蓄电池电量",
                "检查启动继电器"
            ],
            "probability_json": {"fuel_system": 0.6, "ignition_system": 0.3, "battery": 0.1}
        },
        {
            "fault_code_id": fault_codes["E002"].id,
            "forklift_model_id": forklift_model.id,
            "engine_model_id": engine_model.id,
            "symptom": "叉车举升动作缓慢，压力表读数偏低",
            "causes_json": [fault_codes["E002"].id],
            "solutions_json": [
                "检查液压油油位",
                "检查液压泵",
                "检查液压管路是否有泄漏"
            ],
            "probability_json": {"pump_failure": 0.5, "seal_leak": 0.3, "oil_level": 0.2}
        },
        {
            "fault_code_id": fault_codes["E003"].id,
            "forklift_model_id": forklift_model.id,
            "engine_model_id": engine_model.id,
            "symptom": "电气系统 intermittently 断电，安全开关触发",
            "causes_json": [fault_codes["E003"].id],
            "solutions_json": [
                "检查电路布线是否有破损",
                "测试保险丝",
                "检查安全开关状态"
            ],
            "probability_json": {"wiring_damage": 0.4, "fuse": 0.3, "safety_switch": 0.3}
        },
        {
            "fault_code_id": fault_codes["E004"].id,
            "forklift_model_id": forklift_model.id,
            "engine_model_id": engine_model.id,
            "symptom": "刹车踏板行程增大，制动距离延长",
            "causes_json": [fault_codes["E004"].id],
            "solutions_json": [
                "更换刹车片",
                "检查刹车液位",
                "检查刹车分泵"
            ],
            "probability_json": {"pad_wear": 0.5, "fluid_level": 0.3, "sub_pump": 0.2}
        },
        {
            "fault_code_id": fault_codes["E005"].id,
            "forklift_model_id": forklift_model.id,
            "engine_model_id": engine_model.id,
            "symptom": "方向盘游隙过大，转向重量轻",
            "causes_json": [fault_codes["E005"].id],
            "solutions_json": [
                "检查转向拉杆球头", "紧固转向机", "更换转向油缸"
            ],
            "probability_json": {"tie_rod": 0.4, "steering_gear": 0.3, "hydraulic_cylinder": 0.3}
        },
        {
            "fault_code_id": fault_codes["E001"].id,
            "forklift_model_id": forklift_model.id,
            "engine_model_id": engine_model.id,
            "symptom": "发动机异响，转速不稳",
            "causes_json": [fault_codes["E001"].id],
            "solutions_json": [
                "检查机油", "检查气门间隙", "检查活塞环"
            ],
            "probability_json": {"oil_level": 0.4, "valve_clearance": 0.3, "piston_ring": 0.3}
        },
    ]

    # 写入故障树记录
    for tree_data in trees_data:
        stmt = select(FaultTree).filter(
            FaultTree.fault_code_id == tree_data["fault_code_id"],
            FaultTree.forklift_model_id == tree_data["forklift_model_id"],
            FaultTree.engine_model_id == tree_data["engine_model_id"]
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            tree = FaultTree(
                fault_code_id=tree_data["fault_code_id"],
                forklift_model_id=tree_data["forklift_model_id"],
                engine_model_id=tree_data["engine_model_id"],
                symptom=tree_data["symptom"],
                causes_json=tree_data["causes_json"],
                solutions_json=tree_data["solutions_json"],
                probability_json=tree_data["probability_json"]
            )
            db.add(tree)
            db.flush()
            print(f"导入故障树：{tree.id}")
        else:
            print(f"故障树已存在，跳过：{existing.id}")

    db.commit()
    print(f"\n故障树导入完成！共 {len(trees_data)} 条记录")


def main():
    db = SessionLocal()
    try:
        build_fault_trees(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()