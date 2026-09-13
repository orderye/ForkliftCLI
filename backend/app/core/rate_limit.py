"""每日调用次数限制 — 薄壳：实现在 forklift_shared.rate_limit。

免费版每天各功能 3 次，超限返回 429；专业/企业(Ultra)版不限。
Redis 不可用时放行（fail-open）。等级取自本地投影 + 共享 effective_level。
"""
from forklift_shared import rate_limit as _shared
from forklift_shared.subscription_helper import effective_level

from app.config import get_settings
from app.core.database import SessionLocal
from app.models.user import User

settings = get_settings()


def _level_provider(user_id: int) -> str | None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return effective_level(user) if user else None
    finally:
        db.close()


_shared.configure(redis_url=settings.REDIS_URL, level_provider=_level_provider)

check_daily_call = _shared.check_daily_call
reset_redis_client = _shared.reset_redis_client
