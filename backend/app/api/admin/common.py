"""后台管理通用工具：分页 + 审计日志 + ORM 快照"""
from datetime import datetime

from fastapi import HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.admin_audit_logs import AdminAuditLogs
from app.models.copyright_mixin import (
    LICENSE_TYPES,
    NON_COMMERCIAL_LICENSES,
    as_naive_utc,
    naive_utc_now,
)


def paginate(query, page: int, page_size: int) -> dict:
    """对 SQLAlchemy query 做分页，返回 {items, total, page, page_size}"""
    total = query.order_by(None).count()
    items = (
        query.offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def snapshot(obj) -> dict | None:
    """提取 ORM 对象的列字段为可 JSON 序列化的 dict（datetime 转 isoformat）"""
    if obj is None:
        return None
    data = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.name, None)
        if isinstance(value, datetime):
            value = value.isoformat()
        data[col.name] = value
    return data


def client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def write_audit(
    db: Session,
    *,
    admin_id: int,
    action: str,
    target_type: str,
    target_id: int | None,
    before: dict | None = None,
    after: dict | None = None,
    ip: str = "",
) -> None:
    """写入一条管理操作审计日志（独立事务提交，不影响主业务）"""
    db.add(AdminAuditLogs(
        admin_user_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before_json=before,
        after_json=after,
        ip=ip,
    ))
    db.commit()


def validate_copyright(fields: dict, current=None) -> None:
    """校验版权合规字段（MASTER_PLAN 4.3）。

    - create 传 current=None；update 传已有记录以计算生效值
    - license_type 必须在白名单内
    - commercial_use=1 时必须填写版权所有者，且授权类型不可为 user_uploaded/internal_only
    - 新建时 license_expire 必须晚于当前时间（更新可回填历史值）
    """
    license_type = fields.get("license_type")
    if license_type is not None and license_type not in LICENSE_TYPES:
        raise HTTPException(status_code=400, detail=f"非法授权类型：{license_type}")
    effective_type = license_type or (current.license_type if current is not None else "self_owned")

    commercial = fields.get("commercial_use")
    if commercial is None:
        commercial = bool(current.commercial_use) if current is not None else False
    owner = fields.get("copyright_owner")
    if owner is None and current is not None:
        owner = current.copyright_owner

    if commercial:
        if not (owner or "").strip():
            raise HTTPException(status_code=400, detail="可商用资产必须填写版权所有者")
        if effective_type in NON_COMMERCIAL_LICENSES:
            raise HTTPException(status_code=400, detail=f"授权类型 {effective_type} 不可标记为可商用")

    expire = fields.get("license_expire")
    if expire is not None and current is None and as_naive_utc(expire) < naive_utc_now():
        raise HTTPException(status_code=400, detail="授权到期时间必须晚于当前时间")


def safe_like(column, keyword: str):
    """构造 LIKE 查询，自动转义 % 和 _ 通配符防止用户输入干扰匹配范围"""
    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.like(f"%{escaped}%", escape="\\")
