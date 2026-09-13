"""订阅等级与限制辅助 — 薄壳：判定实现在 forklift_shared.subscription_helper。

用户等级判定规则（与 account-system 四级体系一致）：
- 等级权威由 account-service 裁决：登录/心跳把最终生效等级（含企业成员继承）
  同步到本地投影表的 subscription_level / subscription_expires_at。
- 本地 effective_level 只做 normalize（enterprise→ultra 等旧值兼容）+ 过期回落 free。
- to_level_info 保留企业展示字段（本地 enterprises 表为历史遗留，仅展示用）。
"""
from forklift_shared.subscription_helper import (  # noqa: F401
    effective_level,
    is_expired,
    next_expiry,
    parse_dt,
    to_level_info as _shared_to_level_info,
)
from forklift_shared.subscription_levels import (  # noqa: F401
    ENTERPRISE_MAX_ACCOUNTS,
    TRIAL_DAYS,
    get_daily_limit,
    get_forklift_limit,
)
from forklift_shared.subscription_levels import LEVEL_ULTRA


def to_level_info(user) -> dict:
    """订阅信息字典，供 SubscriptionMeOut / UserOut 使用（保留企业字段）。"""
    level = _shared_to_level_info(user)["level"]
    ent = getattr(user, "enterprise_obj", None)
    if level == LEVEL_ULTRA and ent is not None:
        return {
            "level": level,
            "expires_at": ent.plan_expire_at,
            "enterprise_id": ent.id,
            "enterprise_name": ent.name,
        }
    return {
        "level": level,
        "expires_at": user.subscription_expires_at if level != "free" else None,
        "enterprise_id": user.enterprise_id,
        "enterprise_name": ent.name if ent else "",
    }
