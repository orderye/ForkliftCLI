"""幂等初始化超级管理员账号（账户权威在 account-service）

用法：
    # 方式一：.env 配置 ADMIN_PHONE / ADMIN_PASSWORD / ADMIN_NICKNAME 后直接运行
    python scripts/init_admin.py

    # 方式二：命令行参数（优先级高于 .env）
    python scripts/init_admin.py --phone 13800000000 --password 'YourPass123'

说明：
    - 密码与权限归 account-service，本脚本只做转发，本地 users 表只保存业务投影
    - 已存在 → 用 login 校验密码并同步投影（不会重置密码）
    - 不存在 → register 创建超级管理员（必须提供密码，至少 6 位）
    - 重复运行安全，不会产生重复账号
    - 前置条件：account-service 已启动（ACCOUNT_SERVICE_URL）
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.core import account_client
from app.core.database import SessionLocal
from app.models.user import User


def _sync_projection(db, user_info: dict) -> User:
    """与 app/api/auth.py 保持一致的投影同步逻辑"""
    user = db.query(User).filter(User.phone == user_info["phone"]).first()
    fields = {
        "phone": user_info["phone"],
        "email": user_info.get("email") or "",
        "nickname": user_info.get("nickname") or "",
        "avatar": user_info.get("avatar") or "",
        "subscription_level": user_info.get("subscription_level") or "free",
        "subscription_expires_at": user_info.get("subscription_expires_at"),
        "is_active": user_info.get("is_active", True),
        "last_login_at": user_info.get("last_login_at"),
    }
    if not user:
        user = User(id=user_info["id"], **fields)
        db.add(user)
    else:
        for key, value in fields.items():
            if value is not None:
                setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def init_admin(phone: str, password: str | None, nickname: str) -> None:
    db = SessionLocal()
    try:
        if db.query(User).filter(User.phone == phone).first():
            print(f"ℹ️  本地已存在管理员投影 {phone}，改用 login 校验密码")
            try:
                resp = account_client.post("/admin/auth/login", json={"phone": phone, "password": password or ""})
            except Exception as exc:
                print(f"❌ account-service 登录失败：{exc}", file=sys.stderr)
                sys.exit(1)
        else:
            if not password:
                print("❌ 新建超级管理员必须提供密码：--password 参数或 .env 中 ADMIN_PASSWORD", file=sys.stderr)
                sys.exit(1)
            if len(password) < 6:
                print("❌ 密码长度至少 6 位", file=sys.stderr)
                sys.exit(1)
            try:
                resp = account_client.post("/admin/auth/register", json={"phone": phone, "password": password, "nickname": nickname})
            except Exception as exc:
                print(f"❌ account-service 注册失败：{exc}", file=sys.stderr)
                sys.exit(1)

        _sync_projection(db, resp["user"])
        print("✅ 超级管理员已就绪")
        print(f"   手机号: {phone}")
        print(f"   用户ID: {resp['user']['id']}")
        print(f"   昵称:   {resp['user'].get('nickname', '')}")
        print(f"   管理员令牌: {resp.get('access_token', '')[:16]}…")
    finally:
        db.close()


def main():
    settings = get_settings()
    parser = argparse.ArgumentParser(description="初始化/校验超级管理员账号（幂等）")
    parser.add_argument("--phone", default=settings.ADMIN_PHONE, help="管理员手机号")
    parser.add_argument("--password", default=settings.ADMIN_PASSWORD or None, help="初始密码（仅新建时需要）")
    parser.add_argument("--nickname", default=settings.ADMIN_NICKNAME, help="昵称")
    args = parser.parse_args()

    init_admin(phone=args.phone, password=args.password, nickname=args.nickname)


if __name__ == "__main__":
    main()
