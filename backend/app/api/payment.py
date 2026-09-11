"""支付对接（stub 框架）

POST /payment/create  创建支付订单（返回 order_id + 金额 + 第三方参数）
POST /payment/notify  第三方支付回调（stub 验签，更新订单并激活订阅）
GET  /payment/orders  查询当前用户订单历史

说明：
- 当前为通用 stub：platform 区分 ios/android/wechat/alipay，
  真实接入时只需在 create / notify 内实现对应 SDK 调用与签名校验。

【未接线】main.py 未注册本路由，同前缀请求由 app/api/proxy.py 转发给 account-service（账户权威）。保留为本地实现的参考/回退，确认无调用方后可删除。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.push_service import push_subscription_activated
from app.core.security import get_current_user
from app.models.payment import Payment
from app.models.user import User
from app.schemas.subscription import (
    PLAN_PRICES as PRICE_TABLE,
    PaymentCreateIn,
    PaymentCreateOut,
    PaymentNotifyIn,
    PaymentOrderOut,
)

router = APIRouter(prefix="/payment", tags=["支付"])

VALID_PLANS = {"pro", "enterprise"}
VALID_PLATFORMS = {"ios", "android", "wechat", "alipay"}


@router.post("/create", response_model=PaymentCreateOut)
@safe_api
def create_payment(
    data: PaymentCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.plan not in VALID_PLANS:
        raise HTTPException(status_code=400, detail=f"非法套餐：{data.plan}")
    if data.platform not in VALID_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"非法支付平台：{data.platform}")

    amount = PRICE_TABLE.get(data.plan)
    if amount is None:
        raise HTTPException(status_code=400, detail="套餐价格未配置")

    now = datetime.now(timezone.utc)
    payment = Payment(
        user_id=current_user.id,
        plan=data.plan,
        platform=data.platform,
        amount=amount,
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # stub：真实接入时调用对应 SDK 生成预支付订单，写入 payment.payment_params
    payment_params = _build_payment_params(payment)
    payment.payment_params = _dumps_params(payment_params)
    db.commit()
    db.refresh(payment)

    return PaymentCreateOut(
        order_id=payment.id,
        plan=payment.plan,
        amount=payment.amount,
        payment_params=payment_params,
    )


@router.post("/notify", response_model=PaymentOrderOut)
@safe_api
def payment_notify(
    data: PaymentNotifyIn,
    db: Session = Depends(get_db),
):
    """第三方支付异步回调（stub 验签）"""
    payment = db.query(Payment).filter(Payment.id == data.order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="订单不存在")

    if not _verify_notify(data, payment):
        raise HTTPException(status_code=400, detail="回调签名校验失败")

    if data.status != "success":
        payment.status = "failed"
        db.commit()
        db.refresh(payment)
        return PaymentOrderOut.model_validate(payment)

    # 成功：更新订单并激活订阅
    payment.status = "success"
    payment.transaction_id = data.transaction_id
    db.commit()

    from app.api.subscription import PLAN_DURATIONS
    from app.core.subscription_helper import effective_level
    from app.core.subscription_log import log_subscription

    user = db.query(User).filter(User.id == payment.user_id).first()
    if user:
        now = datetime.now(timezone.utc)
        base = user.subscription_expires_at
        if base is not None and base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
        expires_after = (base if base and base > now else now) + PLAN_DURATIONS[payment.plan]

        level_before = effective_level(user)
        expires_before = user.subscription_expires_at
        user.subscription_level = payment.plan
        user.subscription_expires_at = expires_after
        db.commit()

        log_subscription(
            db,
            user_id=user.id,
            action="renew" if level_before == payment.plan else "activate",
            level_before=level_before,
            level_after=payment.plan,
            expires_before=expires_before,
            expires_after=expires_after,
            note=f"payment_id={payment.id} platform={payment.platform}",
        )

        if user.device_token:
            try:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(push_subscription_activated(user.device_token, payment.plan))
                except RuntimeError:
                    asyncio.run(push_subscription_activated(user.device_token, payment.plan))
            except Exception:
                pass

    db.refresh(payment)
    return PaymentOrderOut.model_validate(payment)


@router.get("/orders", response_model=list[PaymentOrderOut])
@safe_api
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return [PaymentOrderOut.model_validate(p) for p in payments]


# ========== 内部辅助（stub） ==========
def _dumps_params(params: dict) -> str:
    import json

    return json.dumps(params, ensure_ascii=False)


def _build_payment_params(payment: Payment) -> dict:
    """生成第三方支付参数（stub，真实接入时替换）"""
    return {
        "order_id": payment.id,
        "amount": payment.amount,
        "plan": payment.plan,
        "platform": payment.platform,
        "stub": True,
    }


def _verify_notify(data: PaymentNotifyIn, payment: Payment) -> bool:
    """校验回调签名（stub，真实接入时实现）"""
    return True
