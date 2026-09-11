"""版权授权到期巡检（MASTER_PLAN 4.3）：打印已过期 / N 天内到期的资产清单。

运行:  python -m scripts.check_license [--days 30]
可挂 cron 定时执行；发现已过期资产时退出码为 1，便于告警。
"""
import argparse
import sys
from pathlib import Path

# 让脚本可以直接以 `python scripts/check_license.py` 方式运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal
from app.services.compliance_service import compliance_summary, expiring_assets


def main() -> int:
    parser = argparse.ArgumentParser(description="版权授权到期巡检")
    parser.add_argument("--days", type=int, default=30, help="提前预警天数（默认 30）")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        items = expiring_assets(db, days=args.days)
        summary = compliance_summary(db)

        expired = [i for i in items if i["expired"]]
        soon = [i for i in items if not i["expired"]]

        print(f"版权巡检（预警窗口 {args.days} 天）")
        print(f"资产总数 {summary['total']} | 已过期 {len(expired)} | "
              f"{args.days} 天内到期 {len(soon)} | 可商用 {summary['commercial_use']}")
        print(f"授权类型分布: {summary['by_license_type']}")

        if expired:
            print("\n[已过期，需下线处理]")
            for i in expired:
                print(f"  - [{i['asset_type']} #{i['id']}] {i['title']} "
                      f"({i['license_type']}, 到期 {i['license_expire']}, {i['copyright_owner'] or '未登记所有者'})")
        if soon:
            print(f"\n[{args.days} 天内到期，需续约或替换]")
            for i in soon:
                print(f"  - [{i['asset_type']} #{i['id']}] {i['title']} "
                      f"({i['license_type']}, 到期 {i['license_expire']}, {i['copyright_owner'] or '未登记所有者'})")

        return 1 if expired else 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
