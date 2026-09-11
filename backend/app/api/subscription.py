"""订阅管理

GET  /subscription/me       查询当前订阅状态
POST /subscription/activate 激活订阅（支付完成后调用）
POST /subscription/cancel   取消自动续订
POST /subscription/renew    手动续费

【未接线】main.py 未注册本路由，同前缀请求由 app/api/proxy.py 转发给 account-service（账户权威）。保留为本地实现的参考/回退，确认无调用方后可删除。
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.security import get_current_user
from app.core.subscription_helper import TRIAL_DAYS, effective_level, to_level_info
from app.core.subscription_log import log_subscription
from app.models.subscription import TrialCard
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionActivateIn,
    SubscriptionActivateOut,
    SubscriptionMeOut,
)

router = APIRouter(prefix="/subscription", tags=["订阅"])

VALID_PLANS = {"pro", "enterprise"}
# 套餐时长：专业版按月，企业版按年
PLAN_DURATIONS = {"pro": timedelta(days=30), "enterprise": timedelta(days=365)}


@router.get("/me", response_model=SubscriptionMeOut)
@safe_api
def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    info = to_level_info(current_user)
    remaining = (
        db.query(TrialCard)
        .filter(TrialCard.owner_uid == current_user.id, TrialCard.status == "unused")
        .count()
    )
    return SubscriptionMeOut(
        level=info["level"],
        expires_at=info["expires_at"],
        enterprise_id=info["enterprise_id"],
        enterprise_name=info["enterprise_name"],
        trial_cards_remaining=remaining,
    )


@router.post("/activate", response_model=SubscriptionActivateOut)
@safe_api
def activate_subscription(
    data: SubscriptionActivateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.plan not in VALID_PLANS:
        raise HTTPException(status_code=400, detail=f"非法套餐：{data.plan}")

    now = datetime.now(timezone.utc)
    base = current_user.subscription_expires_at
    if base is not None and base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)

    expires_after = max(base, now) + PLAN_DURATIONS[data.plan] if base and base > now else now + PLAN_DURATIONS[data.plan]

    level_before = effective_level(current_user)
    expires_before = current_user.subscription_expires_at
    current_user.subscription_level = data.plan
    current_user.subscription_expires_at = expires_after
    db.commit()
    db.refresh(current_user)

    log_subscription(
        db,
        user_id=current_user.id,
        action="renew" if level_before == data.plan else "activate",
        level_before=level_before,
        level_after=data.plan,
        expires_before=expires_before,
        expires_after=expires_after,
        note=f"payment_id={data.payment_id}",
    )
    return SubscriptionActivateOut(level=data.plan, expires_at=expires_after)


@router.post("/cancel")
@safe_api
def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消自动续订（仅标记，到期后不再续费）"""
    if current_user.subscription_level not in VALID_PLANS:
        raise HTTPException(status_code=400, detail="当前无有效订阅")

    level_before = effective_level(current_user)
    log_subscription(
        db,
        user_id=current_user.id,
        action="cancel",
        level_before=level_before,
        level_after=level_before,
        expires_before=current_user.subscription_expires_at,
        expires_after=current_user.subscription_expires_at,
    )
    return {"cancelled": True, "level": level_before, "expires_at": current_user.subscription_expires_at}


@router.post("/renew", response_model=SubscriptionActivateOut)
@safe_api
def renew_subscription(
    data: SubscriptionActivateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动续费：延长当前套餐时长"""
    if current_user.subscription_level not in VALID_PLANS:
        raise HTTPException(status_code=400, detail="当前无有效订阅，请先激活")

    now = datetime.now(timezone.utc)
    base = current_user.subscription_expires_at
    if base is not None and base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    expires_after = (base if base and base > now else now) + PLAN_DURATIONS[current_user.subscription_level]

    level_before = effective_level(current_user)
    expires_before = current_user.subscription_expires_at
    current_user.subscription_expires_at = expires_after
    db.commit()
    db.refresh(current_user)

    log_subscription(
        db,
        user_id=current_user.id,
        action="renew",
        level_before=level_before,
        level_after=current_user.subscription_level,
        expires_before=expires_before,
        expires_after=expires_after,
        note=f"payment_id={data.payment_id}",
    )
    return SubscriptionActivateOut(level=current_user.subscription_level, expires_at=expires_after)


def expire_subscriptions(db: Session) -> int:
    """每日 cron：过期订阅降级为 free，返回处理数量"""
    from app.models.subscription import SubscriptionLog  # noqa: F401 保持导出

    now = datetime.now(timezone.utc)
    expired_users = (
        db.query(User)
        .filter(
            User.subscription_level.in_(list(VALID_PLANS)),
            User.subscription_expires_at < now,
        )
        .all()
    )
    for u in expired_users:
        log_subscription(
            db,
            user_id=u.id,
            action="expire",
            level_before=u.subscription_level,
            level_after="free",
            expires_before=u.subscription_expires_at,
            note="订阅到期自动降级",
        )
        u.subscription_level = "free"
        u.subscription_expires_at = None
    db.commit()
    return len(expired_users)


# 保持模块导出完整，供 trial cron 复用
__all__ = ["router", "expire_subscriptions", "PLAN_DURATIONS"]
_ = TRIAL_DAYS  # 体验卡天数在 trial.py 中使用，此处仅保持引用一致性
