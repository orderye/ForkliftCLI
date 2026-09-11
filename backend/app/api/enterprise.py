"""企业版账户绑定

POST /enterprise/bind_account     绑定账户（升级为 pro）
POST /enterprise/unbind_account   解绑账户（降级为 free）
GET  /enterprise/accounts         查看已绑定账户列表
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.push_service import push_premium_activated, push_subscription_expired
from app.core.security import get_current_user
from app.core.subscription_helper import ENTERPRISE_MAX_ACCOUNTS, effective_level
from app.core.subscription_log import log_subscription
from app.models.enterprise import Enterprise
from app.models.subscription import EnterpriseAccount
from app.models.user import User
from app.schemas.subscription import EnterpriseAccountOut, EnterpriseBindIn

router = APIRouter(prefix="/enterprise", tags=["企业版绑定"])


def _require_enterprise_member(current_user: User, db: Session) -> Enterprise:
    """当前用户必须是有效企业版成员，返回所属企业"""
    if current_user.enterprise_obj is None:
        raise HTTPException(status_code=403, detail="当前账户未关联企业")
    ent = current_user.enterprise_obj
    if ent.plan != "enterprise":
        raise HTTPException(status_code=403, detail="仅企业版可管理绑定账户")
    if ent.plan_expire_at and ent.plan_expire_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="企业版已过期")
    return ent


@router.post("/bind_account")
@safe_api
async def bind_account(
    data: EnterpriseBindIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ent = _require_enterprise_member(current_user, db)

    bound_count = (
        db.query(EnterpriseAccount).filter(EnterpriseAccount.enterprise_id == ent.id).count()
    )
    if bound_count >= ENTERPRISE_MAX_ACCOUNTS:
        raise HTTPException(
            status_code=403,
            detail=f"企业版最多绑定 {ENTERPRISE_MAX_ACCOUNTS} 个账户",
        )

    target = db.query(User).filter(User.phone == data.phone_number).first()
    if not target:
        raise HTTPException(status_code=404, detail="该手机号未注册")

    existing = (
        db.query(EnterpriseAccount)
        .filter(
            EnterpriseAccount.enterprise_id == ent.id,
            EnterpriseAccount.user_id == target.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="该账户已绑定")

    # 记录绑定关系 + 升级为 pro（随企业到期）
    db.add(EnterpriseAccount(enterprise_id=ent.id, user_id=target.id))
    level_before = effective_level(target)
    expires_before = target.subscription_expires_at
    target.enterprise_id = ent.id
    target.subscription_level = "pro"
    target.subscription_expires_at = ent.plan_expire_at
    db.commit()

    log_subscription(
        db,
        user_id=target.id,
        action="enterprise_bind",
        level_before=level_before,
        level_after="pro",
        expires_before=expires_before,
        expires_after=ent.plan_expire_at,
        note=f"enterprise_id={ent.id}",
    )

    if target.device_token:
        await push_premium_activated(target.device_token)

    return {"bound": True, "account_count": bound_count + 1}


@router.post("/unbind_account")
@safe_api
async def unbind_account(
    data: EnterpriseBindIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ent = _require_enterprise_member(current_user, db)

    target = db.query(User).filter(User.phone == data.phone_number).first()
    if not target:
        raise HTTPException(status_code=404, detail="该手机号未注册")

    link = (
        db.query(EnterpriseAccount)
        .filter(
            EnterpriseAccount.enterprise_id == ent.id,
            EnterpriseAccount.user_id == target.id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="该账户未绑定到本企业")

    db.delete(link)
    level_before = effective_level(target)
    expires_before = target.subscription_expires_at
    target.enterprise_id = None
    target.subscription_level = "free"
    target.subscription_expires_at = None
    db.commit()

    log_subscription(
        db,
        user_id=target.id,
        action="enterprise_unbind",
        level_before=level_before,
        level_after="free",
        expires_before=expires_before,
        note=f"enterprise_id={ent.id}",
    )

    if target.device_token:
        await push_subscription_expired(target.device_token)

    account_count = (
        db.query(EnterpriseAccount).filter(EnterpriseAccount.enterprise_id == ent.id).count()
    )
    return {"unbound": True, "account_count": account_count}


@router.get("/accounts", response_model=list[EnterpriseAccountOut])
@safe_api
def list_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ent = _require_enterprise_member(current_user, db)
    links = (
        db.query(EnterpriseAccount)
        .filter(EnterpriseAccount.enterprise_id == ent.id)
        .all()
    )
    result = []
    for link in links:
        u = db.query(User).filter(User.id == link.user_id).first()
        result.append(
            EnterpriseAccountOut(
                user_id=u.id if u else link.user_id,
                phone=u.phone if u else "",
                nickname=u.nickname if u else "",
                bound_at=link.created_at,
            )
        )
    return result
