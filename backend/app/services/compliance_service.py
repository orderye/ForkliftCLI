"""版权合规服务：资产枚举 / 到期巡检汇总（供 admin 看板与巡检脚本复用）"""
from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.ai import KnowledgeDocument
from app.models.copyright_mixin import is_license_expired, naive_utc_now
from app.models.diagram import Diagram
from app.models.model3d import Model3D

# (资产类型, 模型类, 标题字段)
ASSET_SOURCES = [
    ("knowledge_document", KnowledgeDocument, "title"),
    ("diagram", Diagram, "title"),
    ("model3d", Model3D, "name"),
]


def iter_assets(db: Session):
    """遍历全部受版权约束的资产，yield (asset_type, row, title)"""
    for asset_type, model, title_field in ASSET_SOURCES:
        for row in db.query(model).all():
            yield asset_type, row, getattr(row, title_field, "")


def expiring_assets(db: Session, days: int = 30) -> list[dict]:
    """已过期 + days 天内到期的资产清单（按到期时间升序）"""
    deadline = naive_utc_now() + timedelta(days=days)
    items = []
    for asset_type, row, title in iter_assets(db):
        expired = is_license_expired(row.license_expire)
        expiring_soon = row.license_expire is not None and not expired and row.license_expire <= deadline
        if not (expired or expiring_soon):
            continue
        items.append({
            "asset_type": asset_type,
            "id": row.id,
            "title": title or "",
            "source": getattr(row, "source", "") or "",
            "copyright_owner": row.copyright_owner or "",
            "license_type": row.license_type,
            "license_expire": row.license_expire.isoformat() if row.license_expire else None,
            "commercial_use": bool(row.commercial_use),
            "expired": expired,
        })
    items.sort(key=lambda x: x["license_expire"] or "")
    return items


def compliance_summary(db: Session) -> dict:
    """合规看板汇总：授权类型分布 / 已过期 / 30 天内到期 / 可商用"""
    deadline = naive_utc_now() + timedelta(days=30)
    by_type: dict[str, int] = {}
    by_asset: dict[str, dict] = {}
    total = expired = expiring = commercial = 0
    for asset_type, row, _ in iter_assets(db):
        total += 1
        lt = row.license_type or "self_owned"
        by_type[lt] = by_type.get(lt, 0) + 1
        stat = by_asset.setdefault(asset_type, {
            "total": 0, "expired": 0, "expiring_in_30d": 0, "commercial_use": 0,
        })
        stat["total"] += 1
        if row.commercial_use:
            commercial += 1
            stat["commercial_use"] += 1
        if is_license_expired(row.license_expire):
            expired += 1
            stat["expired"] += 1
        elif row.license_expire is not None and row.license_expire <= deadline:
            expiring += 1
            stat["expiring_in_30d"] += 1
    return {
        "total": total,
        "by_license_type": by_type,
        "by_asset": by_asset,
        "expired": expired,
        "expiring_in_30d": expiring,
        "commercial_use": commercial,
    }
