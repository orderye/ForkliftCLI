"""后台-用户管理（代理到 account-service）。

所有用户管理操作（查询、创建、修改、禁用）均由 account-service 权威处理。
ForkliftCLI 负责转发请求并同步本地用户投影（仅保留业务关联所需字段）。
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.admin.common import client_ip, paginate, safe_like, snapshot, write_audit
from app.core.account_client import delete as acct_delete, get as acct_get, post as acct_post, put as acct_put
from app.core.admin_auth import require_admin, AdminPrincipal
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.enterprise import Enterprise
from app.models.user import User

router = APIRouter(prefix="/admin/users", tags=["后台-用户管理"])

# 保持与旧 API 兼容的角色和状态枚举（供本地过滤使用）
VALID_ROLES = {"user", "technician", "operator", "admin"}
VALID_STATUS = {"active", "disabled"}


def _map_account_service_user_to_local(user_data: dict) -> dict:
    """将 account-service 返回的用户数据映射到 ForkliftCLI 本地 User 模型字段。
    仅保留本地表中存在的字段，其余忽略以避免双库漂移。
    """
    mapped = {
        "phone": user_data.get("phone"),
        "email": user_data.get("email", ""),
        "nickname": user_data.get("nickname", ""),
        "avatar": user_data.get("avatar", ""),
        "subscription_level": user_data.get("subscription_level", "free"),
        "subscription_expires_at": user_data.get("subscription_expires_at"),
        "is_active": user_data.get("is_active", True),
    }
    return mapped


def _sync_local_user(user_data: dict, db: Session) -> None:
    """根据 account-service 返回的用户数据更新或创建本地用户投影。
    仅在需要时调用（如登录后、管理员操作后）以保持本地投影新鲜。
    """
    phone = user_data.get("phone")
    if not phone:
        return
    local_user = db.query(User).filter(User.phone == phone).first()
    values = _map_account_service_user_to_local(user_data)
    if local_user:
        for key, value in values.items():
            setattr(local_user, key, value)
    else:
        # 创建新记录，id 由 account-service 决定（但我们不知道），暂时设为 0，后续待改进
        # 注意：这里的 id 可能不匹配，但由于我们仅用于外键和等级缓存，影响有限。
        # 更好的做法是让 account-service 在返回中包含 id，但当前不便改动。
        # 为简单起见，我们这里不创建新记录，而是依赖登录同步。
        # 实际上，后台创建用户时，account-service 会返回包含 id 的完整用户对象。
        # 我们可以读取返回的 id 字段（如果存在）。
        account_id = user_data.get("id")
        if account_id:
            values["id"] = account_id
            local_user = User(**values)
            db.add(local_user)
        else:
            # 没有 id 时，仅更新已有记录（不创建）
            pass
    db.commit()


@router.get("", response_model=dict)
@safe_api
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    role: str | None = None,
    status: str | None = None,
    enterprise_id: int | None = None,
    keyword: str | None = Query(None, description="手机号/昵称模糊搜索"),
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 的用户列表接口，并在返回后同步本地投影。"""
    # 将 ForkliftCLI 的过滤参数映射到 account-service 支持的参数
    params = {
        "page": page,
        "size": page_size,
        "search": keyword,
        # role: account-service 没有直接角色过滤，需要在本地过滤（见下）
        # status: 转换为 is_active
        "is_active": {"active": True, "disabled": False}.get(status) if status else None,
        # enterprise_id: account-service 没有直接企业ID过滤，需要在本地过滤
        # 注册来源、创建时间范围等暂不支持
    }
    # 去掉值为 None 的参数
    params = {k: v for k, v in params.items() if v is not None}

    # 调用 account-service
    resp = acct_get("/admin/users", params=params, token=admin.token)
    # resp 期望为分割响应：{total, page, size, pages, items: [...]}
    items = resp.get("items", [])

    # 本地过滤：role 和 enterprise_id（account-service 不支持）
    if role and role in VALID_ROLES:
        items = [u for u in items if u.get("role") == role]
    if enterprise_id is not None:
        # 需要先填充 enterprise_id（account-service 不返回），这里跳过，后续可改进
        pass

    # 同步本地投影（仅同步当前页的用户，以控制开销）
    for u in items:
        _sync_local_user(u, db)

    return resp


@router.get("/{phone}", response_model=dict)
@safe_api
def get_user(
    phone: str,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 的用户详情接口，并在返回后同步本地投影。"""
    resp = acct_get(f"/admin/users/{phone}", token=admin.token)
    _sync_local_user(resp, db)
    return resp


@router.post("", response_model=dict, status_code=201)
@safe_api
async def create_user(
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 创建用户接口，并在返回后同步本地投影。"""
    # 读取请求体（前端应发送符合 account-service 期望的结构）
    # 为简单起见，我们直接转发原始 JSON
    body = await request.json()
    resp = acct_post("/admin/users", json=body, token=admin.token)
    _sync_local_user(resp, db)
    return resp


@router.put("/{phone}", response_model=dict)
@safe_api
async def update_user(
    phone: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 更新用户接口，并在返回后同步本地投影。"""
    body = await request.json()
    resp = acct_put(f"/admin/users/{phone}", json=body, token=admin.token)
    _sync_local_user(resp, db)
    return resp


@router.delete("/{phone}", response_model=dict)
@safe_api
def disable_user(
    phone: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """代理到 account-service 禁用用户接口，并在返回后同步本地投影（设置 is_active=false）。"""
    resp = acct_delete(f"/admin/users/{phone}", token=admin.token)
    # 禁用后，同步本地投影（account-service 返回的用户对象应已更新 is_active）
    _sync_local_user(resp, db)
    return resp