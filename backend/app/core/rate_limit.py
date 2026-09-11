"""每日调用次数限制（免费版）

用法：在各受限 API 端点顶部调用 check_daily_call(uid, feature)。
免费版每天各功能 3 次，超限返回 429。专业/企业版不限。

Key 设计：user:{uid}:daily:{feature}:{YYYYMMDD}
TTL 计算：到次日 00:00 UTC 的剩余秒数
"""
from datetime import datetime, timedelta

import redis
from fastapi import HTTPException

from app.config import get_settings
from app.core.subscription_helper import effective_level

settings = get_settings()


def _get_redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def check_daily_call(user_id: int, feature: str) -> None:
    """检查并计数；超限 raise HTTPException(429)；免费/过期用户才检查"""
    # 先检查订阅过期降级
    # （由 SubscriptionLog 记录过期事件，subscription_level 保持原值但 effective_level 为 free）
    limit = _compute_limit(user_id, feature)
    if limit is None:
        return  # 不限次

    r = _get_redis()
    today = datetime.utcnow().strftime("%Y%m%d")
    key = f"user:{user_id}:daily:{feature}:{today}"
    count = r.get(key)
    if count is not None and int(count) >= limit:
        raise HTTPException(
            status_code=429,
            detail="今日免费额度已用完，升级专业版解锁无限次",
        )
    pipe = r.pipeline()
    pipe.incr(key)
    now = datetime.utcnow()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    pipe.expire(key, int((midnight - now).total_seconds()))
    pipe.execute()


def _compute_limit(user_id: int, feature: str) -> int | None:
    """根据用户等级返回限制次数（None=不限）"""
    from app.core.database import get_db
    from app.models.user import User

    db_gen = get_db()
    db = next(db_gen)
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        level = effective_level(user)
        from app.core.subscription_helper import get_daily_limit
        return get_daily_limit(level)
    finally:
        db.close()
