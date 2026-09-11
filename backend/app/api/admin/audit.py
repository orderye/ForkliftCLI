"""后台-审计日志查询（仅超级管理员）"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.admin.common import paginate
from app.core.admin_auth import require_super_admin, AdminPrincipal
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.admin_audit_logs import AdminAuditLogs
from app.schemas.admin import AuditLogOut, PageOut

router = APIRouter(prefix="/admin/audit-logs", tags=["后台-审计日志"])


@router.get("", response_model=PageOut[AuditLogOut])
@safe_api
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_user_id: int | None = None,
    action: str | None = None,
    target_type: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_super_admin),
):
    query = db.query(AdminAuditLogs)
    if admin_user_id:
        query = query.filter(AdminAuditLogs.admin_user_id == admin_user_id)
    if action:
        query = query.filter(AdminAuditLogs.action == action)
    if target_type:
        query = query.filter(AdminAuditLogs.target_type == target_type)
    return paginate(query.order_by(AdminAuditLogs.id.desc()), page, page_size)
