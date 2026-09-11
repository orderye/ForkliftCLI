"""订阅等级与限制辅助

用户等级判定规则：
- 企业版用户：所属 enterprise.plan == "enterprise"（绑定账户继承企业等级）
- 个人用户：自身 subscription_level（free / pro），过期则视为 free
- 体验卡：subscription_level == "pro" 且 expires_at 在 7 天内（由激活逻辑写入）
"""
from datetime import datetime, timezone

from app.models.user import User

# 各等级限制
DAILY_CALL_LIMIT = {"free": 3}  # 未列出则不限
FORKLIFT_LIMIT = {"free": 1, "pro": 10}  # 未列出（enterprise）则不限
ENTERPRISE_MAX_ACCOUNTS = 5
TRIAL_DAYS = 7
PRO_PRICE = "¥39/月"
ENTERPRISE_PRICE = "¥899/年"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def is_expired(expires_at) -> bool:
    if expires_at is None:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at < _utcnow()


def effective_level(user: User) -> str:
    """返回用户实际生效的等级：free | pro | enterprise"""
    # 企业版绑定账户
    if user.enterprise_obj and user.enterprise_obj.plan == "enterprise" and not is_expired(
        user.enterprise_obj.plan_expire_at
    ):
        return "enterprise"
    # 个人订阅（pro / enterprise 直接购买）
    level = user.subscription_level or "free"
    if level in ("pro", "enterprise") and not is_expired(user.subscription_expires_at):
        return level
    return "free"


def to_level_info(user: User) -> dict:
    """返回订阅信息字典，供 SubscriptionMeOut / UserOut 使用"""
    level = effective_level(user)
    if level == "enterprise" and user.enterprise_obj:
        return {
            "level": "enterprise",
            "expires_at": user.enterprise_obj.plan_expire_at,
            "enterprise_id": user.enterprise_obj.id,
            "enterprise_name": user.enterprise_obj.name,
        }
    return {
        "level": level,
        "expires_at": user.subscription_expires_at if level != "free" else None,
        "enterprise_id": user.enterprise_id,
        "enterprise_name": user.enterprise_obj.name if user.enterprise_obj else "",
    }


def get_daily_limit(level: str) -> int | None:
    return DAILY_CALL_LIMIT.get(level)


def get_forklift_limit(level: str) -> int | None:
    return FORKLIFT_LIMIT.get(level)
