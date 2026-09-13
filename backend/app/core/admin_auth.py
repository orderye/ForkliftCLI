"""管理员鉴权 — 薄壳：实现在 forklift_shared.admin_auth。

account-service 管理员 token 使用 SECRET_KEY + ":admin" 派生密钥签发，
与用户 token 严格隔离；payload 含 type=="admin"。ForkliftCLI 本地不存管理员，
只做验签 + 通过 account_client 代理管理端数据请求。
AdminPrincipal.id 按 phone 反查本地投影，供审计日志的 admin_user_id 关联。
"""
from forklift_shared.admin_auth import AdminPrincipal, build_admin_deps

from app.config import get_settings

settings = get_settings()


def _resolve_admin_id(phone: str) -> int | None:
    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        row = db.query(User.id).filter(User.phone == phone).first()
        return row[0] if row else None
    finally:
        db.close()


(get_current_admin, require_admin, require_role, require_super_admin) = build_admin_deps(
    secret=settings.SECRET_KEY,
    algorithm=settings.ALGORITHM,
    token_url="/api/v1/admin/auth/login",
    id_resolver=_resolve_admin_id,
)

__all__ = [
    "AdminPrincipal",
    "get_current_admin",
    "require_admin",
    "require_role",
    "require_super_admin",
]
