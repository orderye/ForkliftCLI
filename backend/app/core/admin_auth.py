from datetime import datetime, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.core.security import _decode_token

settings = get_settings()
ALGORITHM = settings.ALGORITHM
# account-service 管理员 token 使用 SECRET_KEY + ":admin" 派生密钥，与用户 token 严格隔离
ADMIN_SECRET = settings.SECRET_KEY + ":admin"
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login", auto_error=False)


class AdminPrincipal:
    """极简管理员身份，供 require_admin/require_super_admin 使用。

    管理员是 account-service 里的独立主体，本地 users 表可能没有对应投影。
    `id` 按 phone 反查本地投影，供审计日志的 admin_user_id 关联；查不到时返回 None
    （外部管理员）。注意不能返回 0 —— admin_user_id 是外键，0 会违反约束。
    """

    def __init__(self, phone: str, role: str, is_super_admin: bool, token: str = ""):
        self.phone = phone
        self.role = role
        self.is_super_admin = is_super_admin
        self.token = token
        self._resolved = False
        self._id: int | None = None

    @property
    def id(self) -> int | None:
        if not self._resolved:
            from app.core.database import SessionLocal

            db = SessionLocal()
            try:
                row = db.query(User.id).filter(User.phone == self.phone).first()
                self._id = row[0] if row else None
            finally:
                db.close()
            self._resolved = True
        return self._id


def _decode_admin_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, ADMIN_SECRET, algorithms=[ALGORITHM])
        if payload.get("type") != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="非管理员令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的管理员认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_admin(
    token: Optional[str] = Depends(admin_oauth2_scheme),
) -> AdminPrincipal:
    """验证 account-service 管理员 JWT 并返回最小权限对象。"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少管理员认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_admin_token(token)
    phone = payload.get("sub")
    role = payload.get("role", "admin")
    is_super_admin = (role == "super_admin")
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌中缺少管理员标识",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AdminPrincipal(phone=phone, role=role, is_super_admin=is_super_admin, token=token)


def is_admin(admin: AdminPrincipal) -> bool:
    return admin.is_super_admin or admin.role in {"admin", "operator"}


def require_admin(
    admin: AdminPrincipal = Depends(get_current_admin),
) -> AdminPrincipal:
    if not is_admin(admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return admin


def require_role(*roles: str):
    allowed = set(roles)

    def dependency(admin: AdminPrincipal = Depends(get_current_admin)) -> AdminPrincipal:
        if admin.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return admin

    return dependency


def require_super_admin(
    admin: AdminPrincipal = Depends(get_current_admin),
) -> AdminPrincipal:
    if not admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限",
        )
    return admin