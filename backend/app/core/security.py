"""用户 JWT 验签 + 投影加载 — 薄壳：实现在 forklift_shared。

token 由 account-service 签发，本地只验签不重签；查本地投影表（users）。
跨端回填：用户若经 forkliftTool 等其他入口注册，本地投影缺失时按 token 从
account-service /public/me 拉取资料补建，保证业务外键即刻可用（改资料/等级
仍以 account-service 为权威，下次登录/心跳会覆盖）。
"""
from fastapi import HTTPException, status as http_status

from forklift_shared.security import build_get_current_user, make_oauth2_scheme
from forklift_shared import security as _shared_security
from forklift_shared.subscription_helper import parse_dt

from app.config import get_settings
from app.core.database import get_db

settings = get_settings()
ALGORITHM = settings.ALGORITHM
oauth2_scheme = make_oauth2_scheme()


def create_access_token(data: dict, expires_delta=None) -> str:
    """测试/兼容用本地签发（旧签名）；生产 token 一律由 account-service 签发。"""
    return _shared_security.create_access_token(
        data,
        secret=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        expires_delta=expires_delta,
    )


def _backfill_projection(db, token: str, phone: str):
    """投影缺失时从 account-service 补建；任何失败都回落为 None（401）。"""
    from app.core.account_client import get as acct_get
    from app.models.user import User

    try:
        info = acct_get("/public/me", token=token)
    except Exception:
        return None
    user_info = info.get("user") or {}
    if not user_info.get("id"):
        return None
    sub = info.get("subscription") or {}
    user = User(
        id=user_info["id"],
        phone=phone,
        email=user_info.get("email") or "",
        nickname=user_info.get("nickname") or "",
        avatar=user_info.get("avatar_url") or "",
        subscription_level=sub.get("level") or "free",
        subscription_expires_at=parse_dt(sub.get("expires_at")),
        is_active=user_info.get("is_active", True),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _load_user(db, token, payload):
    from app.models.user import User

    user = db.query(User).filter(User.phone == payload.get("sub")).first()
    if user is None:
        user = _backfill_projection(db, token, payload.get("sub"))
        if user is None:
            return None
    if not user.is_active:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="账号已停用，请联系管理员",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


get_current_user = build_get_current_user(
    secret=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM,
    scheme=oauth2_scheme,
    db_dependency=get_db,
    loader=_load_user,
)
