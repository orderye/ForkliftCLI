"""体验卡机制

GET  /trial/my-cards  查看我的体验卡
POST /trial/claim     免费用户领取体验卡（输入手机号）

【未接线】main.py 未注册本路由，同前缀请求由 app/api/proxy.py 转发给 account-service（账户权威）。保留为本地实现的参考/回退，确认无调用方后可删除。
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.push_service import push_premium_activated
from app.core.security import get_current_user
from app.core.subscription_helper import TRIAL_DAYS, effective_level
from app.core.subscription_log import log_subscription
from app.models.subscription import TrialCard
from app.models.user import User
from app.schemas.subscription import TrialCardOut, TrialClaimIn

router = APIRouter(prefix="/trial", tags=["体验卡"])


@router.get("/my-cards", response_model=list[TrialCardOut])
@safe_api
def list_my_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cards = (
        db.query(TrialCard)
        .filter(TrialCard.owner_uid == current_user.id)
        .order_by(TrialCard.created_at.desc())
        .all()
    )
    return cards


@router.post("/claim")
@safe_api
async def claim_trial(
    data: TrialClaimIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """免费用户通过输入目标手机号领取体验卡，激活 7 天专业版"""
    if effective_level(current_user) != "free":
        raise HTTPException(status_code=400, detail="仅免费用户可领取体验卡")

    # 查找目标用户（输入的手机号）
    target = db.query(User).filter(User.phone == data.phone).first()
    if not target:
        raise HTTPException(status_code=404, detail="该手机号未注册")

    # 目标用户不能已是 pro / enterprise
    if effective_level(target) != "free":
        raise HTTPException(status_code=400, detail="目标用户已是付费用户，无需领取")

    # 查找目标用户拥有的可用体验卡（未过期、未使用）
    now = datetime.now(timezone.utc)
    card = (
        db.query(TrialCard)
        .filter(
            TrialCard.owner_uid == target.id,
            TrialCard.status == "unused",
            TrialCard.expire_at > now,
        )
        .order_by(TrialCard.created_at.asc())
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="该手机号下无可用体验卡")

    # 激活 7 天专业版
    expires_after = now + timedelta(days=TRIAL_DAYS)
    level_before = effective_level(current_user)
    expires_before = current_user.subscription_expires_at
    current_user.subscription_level = "pro"
    current_user.subscription_expires_at = expires_after

    card.status = "used"
    card.claimed_by = current_user.id
    card.target_phone = data.phone
    db.commit()
    db.refresh(current_user)

    log_subscription(
        db,
        user_id=current_user.id,
        action="trial",
        level_before=level_before,
        level_after="pro",
        expires_before=expires_before,
        expires_after=expires_after,
        note=f"card_id={card.id} owner_uid={card.owner_uid}",
    )

    # 推送激活通知
    if current_user.device_token:
        await push_premium_activated(current_user.device_token)

    return {"activated": True, "level": "pro", "expires_at": expires_after}
