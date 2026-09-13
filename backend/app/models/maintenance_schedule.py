"""Day 6-7 part 2: 灌 10 条故障树 + 杭叉 8/50/200/600/1200h 保养表。

涉及:
  - 已有表 fault_trees(10 条 INSERT)
  - 新表 maintenance_schedules(Base.metadata.create_all 自动建)
  - 杭叉 CQD20H 保养表(~50 条 INSERT)

每条 schedule:
  forklift_model_id, system, item, action, intervals_json, tool, source

intervals_json 形如 [8, 50, 200, 600, 1200] — 多个时间格共享一条,
  action: check / replace / clean / adjust / lubricate / measure
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import Base, engine, SessionLocal  # noqa: E402
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON  # noqa: E402
from app.models.ai import FaultTree  # noqa: E402


# ── 新表 maintenance_schedules ────────────────────────────────
class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id = Column(Integer, primary_key=True, index=True)
    forklift_model_id = Column(Integer, ForeignKey("forklift_models.id"), nullable=False)
    system = Column(String(50), nullable=False)        # 电瓶/控制器/电机/...
    item = Column(String(200), nullable=False)         # 电解液水平
    action = Column(String(20), default="check")       # check/replace/clean/adjust/lubricate/measure
    intervals_json = Column(JSON, default=list)        # [8, 50, 200, 600, 1200]
    tool = Column(String(100), default="")
    source = Column(String(200), default="")


# 自动建表
Base.metadata.create_all(bind=engine, tables=[MaintenanceSchedule.__table__])


# ── 10 条故障树 ──────────────────────────────────────────────
# 每条: (symptom, causes=[(cause, probability)], solutions=[...], fmid)
FAULT_TREES = [
    {
        "fmid": 14,  # 杭叉 CPCD30(代表 CPC/CPCD 系列)
        "symptom": "货叉自动缓慢下滑(空载或轻载)",
        "causes": [
            ("起升滑阀磨损,阀体与阀杆间隙过大,压力油经此泄漏回油箱", "高"),
            ("起升油缸活塞密封圈损坏,高压油从下腔渗漏到上腔", "高"),
            ("管路接头松动或密封件老化", "中"),
        ],
        "solutions": [
            "拆下提升缸上部回油管与油箱的连接端",
            "操作起升手柄提升货物,观察该回油管",
            "若有油持续流出 → 活塞密封圈泄漏 → 更换密封件",
            "若无油流出 → 起升换向阀问题 → 检修或更换多路阀",
        ],
        "source": "龙工叉车液压系统.txt 第 12 段(常见故障与诊断)",
    },
    {
        "fmid": 14,
        "symptom": "起升无力,不能起升额定载荷",
        "causes": [
            ("液压油量不足或油液污染/粘度低", "高"),
            ("齿轮油泵内部磨损,输出压力不足", "高"),
            ("溢流阀压力设定过低或阀芯卡滞", "中"),
            ("多路换向阀内漏", "中"),
            ("起升油缸内漏(活塞密封损坏)", "中"),
            ("液压油滤清器严重堵塞", "低"),
            ("油温过高,油液粘度下降,密封性能变差", "低"),
        ],
        "solutions": [
            "检查液压油油位、油质;补油或换油",
            "用油压表测系统压力,与标定值对比",
            "压力低 → 检查齿轮泵,异常噪音或压力不足时更换",
            "压力正常但起升无力 → 拆检多路阀,看阀芯磨损/弹簧",
            "油缸内泄测试:负载保持 5 分钟,下沉 > 50mm 即更换密封",
            "清洗或更换液压油滤清器",
        ],
        "source": "龙工叉车液压系统.txt 第 13-19 段",
    },
    {
        "fmid": 56,  # 杭叉 CQD20H
        "symptom": "货叉架、门架自行倾斜",
        "causes": [
            ("倾斜油缸与密封圈过度磨损", "高"),
            ("多路阀控制阀杆弹簧失灵", "中"),
        ],
        "solutions": [
            "更换活塞密封圈或油缸",
            "更换多路阀控制阀杆弹簧",
        ],
        "source": "前移式叉车使用说明书.txt 第二部分 5.起升系统 故障表",
    },
    {
        "fmid": 56,
        "symptom": "货叉架升降倾斜不灵活",
        "causes": [
            ("活塞卡住缸壁或活塞杆弯曲", "高"),
            ("缸内积垢过多", "中"),
        ],
        "solutions": [
            "更换损坏件",
            "清洗油缸",
        ],
        "source": "前移式叉车使用说明书.txt 第二部分 5.起升系统",
    },
    {
        "fmid": 56,
        "symptom": "货叉架升降不平滑",
        "causes": [
            ("货叉架总成调整不当", "高"),
            ("导轨润滑不足", "中"),
            ("起升油缸内有空气", "中"),
        ],
        "solutions": [
            "调整槽钢导轨位置",
            "导轨添加润滑脂",
            "反复升降 5-10 次排气",
        ],
        "source": "前移式叉车使用说明书.txt 第二部分 5.起升系统",
    },
    {
        "fmid": 56,
        "symptom": "转向操纵不灵活",
        "causes": [
            ("转向链条张紧度不合适", "高"),
            ("链条碰擦", "中"),
        ],
        "solutions": [
            "调整调整螺栓",
            "检修链条",
        ],
        "source": "前移式叉车使用说明书.txt 第二部分 2.转向系统",
    },
    {
        "fmid": 56,
        "symptom": "无转向",
        "causes": [
            ("转向马达损坏或不工作", "高"),
            ("转向器故障", "高"),
            ("优先阀故障", "中"),
            ("油泵故障", "中"),
            ("油路堵塞", "中"),
        ],
        "solutions": [
            "检修转向马达",
            "检修转向器",
            "检修优先阀",
            "检修油泵",
            "检查清洗油路",
        ],
        "source": "前移式叉车使用说明书.txt 第二部分 2.转向系统",
    },
    {
        "fmid": 56,
        "symptom": "转向噪音",
        "causes": [
            ("转台轴承润滑不充足", "高"),
            ("转台轴承破损", "中"),
            ("转台轴向松动", "中"),
        ],
        "solutions": [
            "加注润滑脂",
            "更换转台轴承",
            "调整轴承预紧度",
        ],
        "source": "前移式叉车使用说明书.txt 第二部分 2.转向系统",
    },
    {
        "fmid": 56,
        "symptom": "踩加速器叉车不行走",
        "causes": [
            ("方向开关接触不良", "高"),
            ("手刹开关粘连", "高"),
            ("加速器故障", "中"),
            ("控制器发生故障", "中"),
            ("安全踏板开关断路", "中"),
            ("断线/插接件接触不良", "中"),
            ("保险丝断", "低"),
        ],
        "solutions": [
            "检修方向开关",
            "检修手刹开关",
            "检修或更换加速器",
            "检修或更换控制器",
            "检修安全踏板开关",
            "重新联接/更换插接件",
            "更换保险丝",
        ],
        "source": "前移式叉车使用说明书.txt 第二部分 6.2 电气系统常见故障",
    },
    {
        "fmid": 56,
        "symptom": "打开钥匙开关无电压",
        "causes": [
            ("钥匙开关接触不良", "高"),
            ("蓄电池接头松动", "高"),
            ("断线/插接件接触不良", "中"),
        ],
        "solutions": [
            "更换钥匙开关",
            "拧紧连接螺栓",
            "重新联接/更换插接件",
        ],
        "source": "前移式叉车使用说明书.txt 第二部分 6.2 电气系统常见故障",
    },
]
assert len(FAULT_TREES) == 10


# ── 杭叉 CQD20H 保养表(基于 8/50/200/600/1200h 维护时间表) ─
# 每条: (system, item, action, intervals, tool)
# intervals: 出现该动作的时间格
# 〇=check, ×=replace, 〇或×=check_or_replace
CQD_SCHEDULE = [
    # ====== 电瓶 ======
    {"system": "电瓶", "item": "电解液水平", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": "目测"},
    {"system": "电瓶", "item": "电解液比重", "action": "check", "intervals": [50, 200, 600, 1200], "tool": "比重计"},
    {"system": "电瓶", "item": "电瓶电量", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "电瓶", "item": "接线端子是否松动", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "电瓶", "item": "连接线是否松动", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "电瓶", "item": "电瓶表面清洁", "action": "clean", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "电瓶", "item": "电瓶表面有否放置工具", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "电瓶", "item": "通风盖是否拧紧,通风口是否畅通", "action": "check", "intervals": [50, 200, 600, 1200], "tool": ""},
    {"system": "电瓶", "item": "远离烟火(操作警示)", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},

    # ====== 控制器 ======
    {"system": "控制器", "item": "检查接触器触点的磨损烧蚀状况", "action": "check", "intervals": [600, 1200], "tool": ""},
    {"system": "控制器", "item": "检查接触器机械运动情况是否良好", "action": "check", "intervals": [600, 1200], "tool": ""},
    {"system": "控制器", "item": "检查安全踏板微动开关运作是否正常", "action": "check", "intervals": [600, 1200], "tool": ""},
    {"system": "控制器", "item": "检查电机、电池及功率单元之间的连接状况", "action": "check", "intervals": [600, 1200], "tool": ""},
    {"system": "控制器", "item": "检查表面清滤情况,必要时用压缩空气吹净", "action": "clean", "intervals": [200, 600, 1200], "tool": "压缩空气"},

    # ====== 电机 ======
    {"system": "电机", "item": "清除电机壳上异物", "action": "clean", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "电机", "item": "清洗或更换轴承", "action": "check_or_replace", "intervals": [1200], "tool": ""},
    {"system": "电机", "item": "碳刷、整流子是否磨损,弹簧力是否正常", "action": "check_or_replace", "intervals": [600, 1200], "tool": ""},
    {"system": "电机", "item": "接线是否正确、牢靠", "action": "check", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "电机", "item": "清刷换向片小沟及换向器表面碳精粉末", "action": "clean", "intervals": [600, 1200], "tool": ""},

    # ====== 传动系统(变速箱) ======
    {"system": "传动系统", "item": "变速箱是否有噪音", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": "听"},
    {"system": "传动系统", "item": "变速箱换油", "action": "replace", "intervals": [1200], "tool": ""},
    {"system": "传动系统", "item": "检查渗漏", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},

    # ====== 车轮 ======
    {"system": "车轮", "item": "检查车轮是否磨损裂缝", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": "目测"},
    {"system": "车轮", "item": "车轮紧固件是否松动", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "车轮", "item": "检查车轮轴承预紧度", "action": "check", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "车轮", "item": "车轮轴承润滑", "action": "lubricate", "intervals": [200, 600, 1200], "tool": "润滑脂"},
    {"system": "车轮", "item": "检查是否有噪音", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "车轮", "item": "检查是否有杂绳索缠绕车轮", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},

    # ====== 转向系统 ======
    {"system": "转向系统", "item": "方向盘检查间隙", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "转向系统", "item": "检查轴向松动", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "转向系统", "item": "检查径向松动", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "转向系统", "item": "检查操作状况", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "转向系统", "item": "转向器检查安装螺栓是否松动", "action": "check", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "转向系统", "item": "链条张紧度检查,必要时调整", "action": "adjust", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "转向系统", "item": "链条润滑(加机械油)", "action": "lubricate", "intervals": [200, 600, 1200], "tool": "机械油"},

    # ====== 液压系统 ======
    {"system": "液压系统", "item": "液压油箱油量检查", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": "目测"},
    {"system": "液压系统", "item": "液压油箱换油(首保半年,之后 1200-1500h 或每年)", "action": "replace", "intervals": [1200], "tool": ""},
    {"system": "液压系统", "item": "清理吸油滤芯", "action": "clean", "intervals": [1200], "tool": ""},
    {"system": "液压系统", "item": "排除油箱内异物", "action": "check", "intervals": [1200], "tool": ""},
    {"system": "液压系统", "item": "控制阀杆连接是否松动", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "液压系统", "item": "控制阀杆操作情况", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "液压系统", "item": "多路阀漏油检查", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "液压系统", "item": "安全阀和倾斜自锁阀操作情况", "action": "check", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "液压系统", "item": "测量安全阀压力", "action": "measure", "intervals": [1200], "tool": "油压表"},
    {"system": "液压系统", "item": "管路接头渗漏/松动/破裂/变形/损伤", "action": "check", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "液压系统", "item": "更换液压管(1-2年)", "action": "replace", "intervals": [1200], "tool": ""},
    {"system": "液压系统", "item": "液压泵是否漏油或有杂音", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": "听"},
    {"system": "液压系统", "item": "油马达是否漏油或有杂音", "action": "check", "intervals": [200, 600, 1200], "tool": "听"},
    {"system": "液压系统", "item": "优先阀工作情况", "action": "check", "intervals": [200, 600, 1200], "tool": ""},

    # ====== 制动系统 ======
    {"system": "制动系统", "item": "制动踏板空行程", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": "刻度尺"},
    {"system": "制动系统", "item": "踏板行程", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "制动系统", "item": "制动踏板操作情况", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "制动系统", "item": "制动管路是否有空气", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "制动系统", "item": "停车制动安全可靠并有足够行程", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "制动系统", "item": "操纵性能(杆/拉索)", "action": "check", "intervals": [8, 50, 200, 600, 1200], "tool": ""},
    {"system": "制动系统", "item": "操纵机构连接是否松动", "action": "check", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "制动系统", "item": "管路损伤、渗漏、破裂", "action": "check", "intervals": [200, 600, 1200], "tool": ""},
    {"system": "制动系统", "item": "总泵、活塞皮碗、单向阀磨损/损伤(更换)", "action": "replace", "intervals": [1200], "tool": ""},

    # ====== 起升/门架/货叉(从手册 7.3 章节摘) ======
    {"system": "起升系统", "item": "链条张紧状态,是否变形/损伤/锈蚀", "action": "check", "intervals": [50, 200, 600, 1200], "tool": ""},
    {"system": "起升系统", "item": "货叉变形、开裂、损伤情况", "action": "check", "intervals": [50, 200, 600, 1200], "tool": "目测"},
    {"system": "起升系统", "item": "门架导轨润滑", "action": "lubricate", "intervals": [200, 600, 1200], "tool": "润滑脂"},
    {"system": "起升系统", "item": "定期更换关键安全零件(参照 CQD 关键件清单)", "action": "replace", "intervals": [1200], "tool": ""},
]


def _upsert_fault_tree(db, f) -> tuple[FaultTree, str]:
    """幂等:以 symptom + fmid 唯一。"""
    existing = (
        db.query(FaultTree)
        .filter(
            FaultTree.forklift_model_id == f["fmid"],
            FaultTree.symptom == f["symptom"],
        )
        .first()
    )
    causes_json = [{"cause": c, "probability": p} for c, p in f["causes"]]
    probability_json = {c: p for c, p in f["causes"]}
    if existing:
        existing.causes_json = causes_json
        existing.solutions_json = f["solutions"]
        existing.probability_json = probability_json
        return existing, "UPDATE"
    ft = FaultTree(
        forklift_model_id=f["fmid"],
        symptom=f["symptom"],
        causes_json=causes_json,
        solutions_json=f["solutions"],
        probability_json=probability_json,
    )
    db.add(ft)
    db.flush()
    return ft, "INSERT"


def _upsert_schedule(db, fmid: int, item: dict, source: str) -> tuple[MaintenanceSchedule, str]:
    """幂等:以 fmid + system + item + action 唯一。"""
    existing = (
        db.query(MaintenanceSchedule)
        .filter(
            MaintenanceSchedule.forklift_model_id == fmid,
            MaintenanceSchedule.system == item["system"],
            MaintenanceSchedule.item == item["item"],
            MaintenanceSchedule.action == item["action"],
        )
        .first()
    )
    if existing:
        existing.intervals_json = item["intervals"]
        existing.tool = item.get("tool", "")
        return existing, "UPDATE"
    s = MaintenanceSchedule(
        forklift_model_id=fmid,
        system=item["system"],
        item=item["item"],
        action=item["action"],
        intervals_json=item["intervals"],
        tool=item.get("tool", ""),
        source=source,
    )
    db.add(s)
    db.flush()
    return s, "INSERT"


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fault-trees-only", action="store_true")
    parser.add_argument("--schedule-only", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        fmid = 56  # 杭叉 CQD20H

        # ── Part 1: 故障树 ──
        if not args.schedule_only:
            print("=" * 60)
            print("Part 1: fault_trees 10 条")
            print("=" * 60)
            ft_insert = ft_update = 0
            for f in FAULT_TREES:
                if args.dry_run:
                    print(f"  DRY: [{f['fmid']}] {f['symptom']}  ({len(f['causes'])} causes, {len(f['solutions'])} steps)")
                else:
                    _, action = _upsert_fault_tree(db, f)
                    if action == "INSERT":
                        ft_insert += 1
                    else:
                        ft_update += 1
                    print(f"  [{action}] [{f['fmid']}] {f['symptom']}")
            if not args.dry_run:
                db.commit()
                print(f"  → INSERT={ft_insert}  UPDATE={ft_update}")

        # ── Part 2: 保养表 ──
        if not args.fault_trees_only:
            print()
            print("=" * 60)
            print(f"Part 2: maintenance_schedules {len(CQD_SCHEDULE)} 条(杭叉 CQD20H)")
            print("=" * 60)
            source = "前移式叉车使用说明书.txt 定期维护时间表(2026-09-12 提取)"
            s_insert = s_update = 0
            for item in CQD_SCHEDULE:
                if args.dry_run:
                    intervals = ",".join(str(x) for x in item["intervals"])
                    print(f"  DRY: {item['system']:<8} {item['action']:<16} {item['item']:<35} [{intervals}]")
                else:
                    _, action = _upsert_schedule(db, fmid, item, source)
                    if action == "INSERT":
                        s_insert += 1
                    else:
                        s_update += 1
            if not args.dry_run:
                db.commit()
                print(f"  → INSERT={s_insert}  UPDATE={s_update}")

        # ── 校验 ──
        if not args.dry_run:
            print()
            print("=" * 60)
            print("DB 校验")
            print("=" * 60)
            ft_count = db.query(FaultTree).count()
            ms_count = db.query(MaintenanceSchedule).count()
            print(f"  fault_trees 总行数: {ft_count}")
            print(f"  maintenance_schedules 总行数: {ms_count}")
            # 按 system 统计
            from sqlalchemy import func
            sys_stats = (
                db.query(MaintenanceSchedule.system, func.count(MaintenanceSchedule.id))
                .group_by(MaintenanceSchedule.system)
                .all()
            )
            print(f"  保养表按系统:")
            for sys_name, n in sys_stats:
                print(f"    {sys_name}: {n}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
