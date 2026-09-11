"""每日调用次数限制（免费版）

用法：在各受限 API 端点顶部调用 check_daily_call(uid, feature)。
免费版每天各功能 3 次，超限返回 429。专业/企业版不限。

Key 设计：user:{uid}:daily:{feature}:{YYYYMMDD}
TTL 计算：到次日 00:00 UTC 的剩余秒数

失败策略：Redis 不可用时放行（fail-open）并记日志。速率限制只是免费额度门禁，
不该因为缓存层故障把付费功能一起打挂。
"""
import logging
from datetime import datetime, timedelta

import redis
from fastapi import HTTPException

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    """惰性建连并复用；测试可 monkeypatch 本函数注入替身"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def reset_redis_client() -> None:
    """测试或配置变更后清空缓存的连接"""
    global _redis_client
    _redis_client = None


def check_daily_call(user_id: int, feature: str) -> None:
    """检查并计数；超限 raise HTTPException(429)；免费/过期用户才检查"""
    # 过期用户由 effective_level 降级为 free，额度随之收紧
    limit = _compute_limit(user_id, feature)
    if limit is None:
        return  # 不限次

    try:
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
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - Redis 故障一律放行，见模块说明
        logger.warning("daily call limit skipped (%s): %s", feature, exc)


def _compute_limit(user_id: int, feature: str) -> int | None:
    """根据用户等级返回限制次数（None=不限）"""
    from app.core.database import SessionLocal
    from app.core.subscription_helper import effective_level, get_daily_limit
    from app.models.user import User

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return get_daily_limit(effective_level(user))
    finally:
        db.close()
