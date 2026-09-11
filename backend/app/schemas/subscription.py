"""订阅/商业化相关 Schema"""
from datetime import datetime

from pydantic import BaseModel


class SubscriptionMeOut(BaseModel):
    level: str
    expires_at: datetime | None = None
    enterprise_id: int | None = None
    enterprise_name: str = ""
    trial_cards_remaining: int = 0

    class Config:
        from_attributes = True


class SubscriptionActivateIn(BaseModel):
    plan: str  # pro | enterprise
    payment_id: str = ""
    receipt: str = ""


class SubscriptionActivateOut(BaseModel):
    level: str
    expires_at: datetime | None = None


class TrialCardOut(BaseModel):
    id: int
    status: str
    expire_at: datetime | None = None
    target_phone: str = ""

    class Config:
        from_attributes = True


class TrialClaimIn(BaseModel):
    phone: str


class EnterpriseBindIn(BaseModel):
    phone_number: str


class EnterpriseAccountOut(BaseModel):
    user_id: int
    phone: str = ""
    nickname: str = ""
    bound_at: datetime | None = None


# ========== 支付 ==========
class PaymentCreateIn(BaseModel):
    plan: str  # pro | enterprise
    platform: str = "wechat"  # ios | android | wechat | alipay


class PaymentCreateOut(BaseModel):
    order_id: int
    plan: str
    amount: float
    payment_params: dict = {}


class PaymentNotifyIn(BaseModel):
    order_id: int
    transaction_id: str = ""
    status: str = "success"  # success | failed


class PaymentOrderOut(BaseModel):
    id: int
    user_id: int
    plan: str
    platform: str
    amount: float
    status: str
    transaction_id: str = ""
    created_at: datetime | None = None

    class Config:
        from_attributes = True


PLAN_PRICES = {"pro": 39.0, "enterprise": 899.0}
