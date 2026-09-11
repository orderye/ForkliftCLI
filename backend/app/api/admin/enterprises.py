"""后台-企业管理（代理到 account-service）。

所有企业创建/修改/删除/成员绑定操作均由 account-service 权威处理。
ForkliftCLI 负责转发请求并同步本地企业投影。
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.admin.common import client_ip, paginate, safe_like, snapshot, write_audit
from app.core.account_client import delete as acct_delete, get as acct_get, post as acct_post, put as acct_put
from app.core.admin_auth import require_admin, AdminPrincipal
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.enterprise import Enterprise
from app.models.user import User

router = APIRouter(prefix="/admin/enterprises", tags=["后台-企业管理"])

VALID_PLANS = {"free", "pro", "enterprise"}
VALID_STATUS = {"active", "disabled"}


def _sync_local_enterprise(ent_data: dict, db: Session) -> None:
    """根据 account-service 返回的企业数据更新或创建本地企业投影。"""
    ent_id = ent_data.get("id")
    if not ent_id:
        return
    local_ent = db.query(Enterprise).filter(Enterprise.id == ent_id).first()
    if local_ent:
        for key, value in ent_data.items():
            if hasattr(local_ent, key):
                setattr(local_ent, key, value)
    else:
        # 创建新记录
        local_ent = Enterprise(**ent_data)
        db.add(local_ent)
    db.commit()


def _fill_user_counts(db: Session, enterprises: list[Enterprise]) -> None:
    """为本地企业列表填充 user_count（动态属性，供 schema 读取）。"""
    ids = [e.id for e in enterprises]
    counts = dict(
        db.query(User.enterprise_id, func.count(User.id))
        .filter(User.enterprise_id.in_(ids))
        .group_by(User.enterprise_id)
        .all()
    ) if ids else {}
    for e in enterprises:
        e.user_count = counts.get(e.id, 0)


@router.get("", response_model=dict)
@safe_api
def list_enterprises(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str | None = None,
    plan: str | None = None,
    keyword: str | None = Query(None, description="企业名/编号模糊搜索"),
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 的企业列表接口，并在返回后同步本地投影。"""
    params = {
        "page": page,
        "size": page_size,
        "status": status,
        "plan": plan,
        "keyword": keyword,
    }
    params = {k: v for k, v in params.items() if v is not None}

    resp = acct_get("/admin/enterprises", params=params, token=admin.token)
    items = resp.get("items", [])

    # 同步本地企业投影
    for ent in items:
        _sync_local_enterprise(ent, db)

    return resp


@router.get("/{enterprise_id}", response_model=dict)
@safe_api
def get_enterprise(
    enterprise_id: int,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 的企业详情接口，并在返回后同步本地投影。"""
    resp = acct_get(f"/admin/enterprises/{enterprise_id}", token=admin.token)
    _sync_local_enterprise(resp, db)
    return resp


@router.post("", response_model=dict, status_code=201)
@safe_api
async def create_enterprise(
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 创建企业接口，并在返回后同步本地投影。"""
    body = await request.json()
    resp = acct_post("/admin/enterprises", json=body, token=admin.token)
    _sync_local_enterprise(resp, db)
    return resp


@router.put("/{enterprise_id}", response_model=dict)
@safe_api
async def update_enterprise(
    enterprise_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 更新企业接口，并在返回后同步本地投影。"""
    body = await request.json()
    resp = acct_put(f"/admin/enterprises/{enterprise_id}", json=body, token=admin.token)
    _sync_local_enterprise(resp, db)
    return resp


@router.delete("/{enterprise_id}", response_model=dict)
@safe_api
def delete_enterprise(
    enterprise_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 删除企业接口，并在返回后同步本地投影。"""
    resp = acct_delete(f"/admin/enterprises/{enterprise_id}", token=admin.token)
    # 删除后，同步本地企业投影（account-service 返回的响应可能不含完整企业数据，这里仅标记）
    # 如果 account-service 返回了被删除的企业信息，则同步；否则忽略
    if isinstance(resp, dict) and resp.get("id"):
        _sync_local_enterprise(resp, db)
    return resp