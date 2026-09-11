"""后台-版权合规（MASTER_PLAN 4.3）：汇总看板 + 到期清单 + CSV 导出"""
import csv
import io

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.admin_auth import require_admin, AdminPrincipal
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.copyright_mixin import is_license_expired
from app.services.compliance_service import compliance_summary, expiring_assets, iter_assets

router = APIRouter(prefix="/admin/compliance", tags=["后台-版权合规"])

CSV_HEADERS = [
    "asset_type", "id", "title", "source", "copyright_owner",
    "license_type", "license_expire", "commercial_use", "expired",
]


@router.get("/summary")
@safe_api
def get_compliance_summary(db: Session = Depends(get_db), _: AdminPrincipal = Depends(require_admin)):
    """合规看板：各授权类型数量、已过期、30 天内到期、可商用资产数"""
    return compliance_summary(db)


@router.get("/expiring")
@safe_api
def list_expiring(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    """已过期 + days 天内到期的资产清单"""
    items = expiring_assets(db, days=days)
    return {"items": items, "total": len(items)}


@router.get("/export")
@safe_api
def export_csv(db: Session = Depends(get_db), _: AdminPrincipal = Depends(require_admin)):
    """导出全部资产版权信息 CSV（供法务审查）"""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_HEADERS)
    for asset_type, row, title in iter_assets(db):
        writer.writerow([
            asset_type,
            row.id,
            title or "",
            getattr(row, "source", "") or "",
            row.copyright_owner or "",
            row.license_type or "",
            row.license_expire.isoformat() if row.license_expire else "",
            bool(row.commercial_use),
            is_license_expired(row.license_expire),
        ])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=copyright_compliance.csv"},
    )
