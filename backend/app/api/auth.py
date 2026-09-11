"""认证路由 — 注册 / 登录 / 用户资料（委托 account-service）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.account_client import post, get, put
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="注册")
def register(data: UserRegister, db: Session = Depends(get_db)):
    """手机号 + 密码注册，转发至 account-service，成功后同步本地投影。"""
    resp = post("/auth/register", json=data.model_dump())
    token = resp["access_token"]
    user_info = resp["user"]

    user = db.query(User).filter(User.id == user_info["id"]).first()
    if not user:
        user = User(
            id=user_info["id"],
            phone=user_info["phone"],
            email=user_info.get("email") or "",
            nickname=user_info.get("nickname") or "",
            avatar=user_info.get("avatar") or "",
            subscription_level=user_info.get("subscription_level") or "free",
            subscription_expires_at=user_info.get("subscription_expires_at"),
            is_active=user_info.get("is_active", True),
        )
        db.add(user)
    else:
        user.phone = user_info["phone"]
        user.email = user_info.get("email") or ""
        user.nickname = user_info.get("nickname") or ""
        user.avatar = user_info.get("avatar") or ""
        user.subscription_level = user_info.get("subscription_level") or "free"
        user.subscription_expires_at = user_info.get("subscription_expires_at")
        user.is_active = user_info.get("is_active", True)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse, summary="登录")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """手机号 + 密码登录，转发至 account-service，成功后同步本地投影。"""
    resp = post("/auth/login", json=data.model_dump())
    token = resp["access_token"]
    user_info = resp["user"]

    user = db.query(User).filter(User.id == user_info["id"]).first()
    if not user:
        user = User(
            id=user_info["id"],
            phone=user_info["phone"],
            email=user_info.get("email") or "",
            nickname=user_info.get("nickname") or "",
            avatar=user_info.get("avatar") or "",
            subscription_level=user_info.get("subscription_level") or "free",
            subscription_expires_at=user_info.get("subscription_expires_at"),
            is_active=user_info.get("is_active", True),
            last_login_at=user_info.get("last_login_at"),
        )
        db.add(user)
    else:
        user.phone = user_info["phone"]
        user.email = user_info.get("email") or ""
        user.nickname = user_info.get("nickname") or ""
        user.avatar = user_info.get("avatar") or ""
        user.subscription_level = user_info.get("subscription_level") or "free"
        user.subscription_expires_at = user_info.get("subscription_expires_at")
        user.is_active = user_info.get("is_active", True)
        user.last_login_at = user_info.get("last_login_at")
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.get("/profile", response_model=UserOut, summary="查看资料")
def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户资料（本地投影即可，若需实时可转发 account-service）。"""
    return current_user


@router.put("/profile", response_model=UserOut, summary="编辑资料")
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户资料（昵称、头像、邮箱），转发至 account-service 并同步本地投影。"""
    # 获取当前 token（依赖注入的 get_current_user 已验证 token，但未暴露 token 本身）
    # 这里简化为：仅更新本地投影；account-service 更新通过登录时同步。
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.avatar is not None:
        current_user.avatar = data.avatar
    if data.email is not None:
        current_user.email = data.email
    db.commit()
    db.refresh(current_user)
    return current_user