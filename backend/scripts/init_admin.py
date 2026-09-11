"""幂等初始化超级管理员账号

用法：
    # 方式一：.env 配置 ADMIN_PHONE / ADMIN_PASSWORD / ADMIN_NICKNAME 后直接运行
    python scripts/init_admin.py

    # 方式二：命令行参数（优先级高于 .env）
    python scripts/init_admin.py --phone 13800000000 --password 'YourPass123'

说明：
    - 账号已存在 → 提升为 role=admin、is_super_admin=True、status=active（不重置密码）
    - 账号不存在 → 创建新超级管理员（必须提供密码，至少 6 位）
    - 重复运行安全，不会产生重复账号
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User


def init_admin(phone: str, password: str | None, nickname: str) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()

        if user:
            changed = []
            if user.role != "admin":
                user.role = "admin"
                changed.append("role=admin")
            if not user.is_super_admin:
                user.is_super_admin = True
                changed.append("is_super_admin=True")
            if user.status != "active":
                user.status = "active"
                changed.append("status=active")
            if nickname and user.nickname != nickname:
                user.nickname = nickname
                changed.append(f"nickname={nickname}")

            if changed:
                db.commit()
                print(f"✅ 账号 {phone} 已存在，已提升：{', '.join(changed)}")
            else:
                print(f"✅ 账号 {phone} 已是超级管理员，无需变更")
            print(f"   用户ID: {user.id}  昵称: {user.nickname}")
            return

        if not password:
            print("❌ 新建超级管理员必须提供密码：--password 参数或 .env 中 ADMIN_PASSWORD", file=sys.stderr)
            sys.exit(1)
        if len(password) < 6:
            print("❌ 密码长度至少 6 位", file=sys.stderr)
            sys.exit(1)

        user = User(
            phone=phone,
            password_hash=hash_password(password),
            nickname=nickname or f"管理员{phone[-4:]}",
            role="admin",
            is_super_admin=True,
            status="active",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ 超级管理员创建成功")
        print(f"   手机号: {phone}")
        print(f"   用户ID: {user.id}")
        print(f"   昵称:   {user.nickname}")
        print(f"   角色:   admin (is_super_admin=True)")
    finally:
        db.close()


def main():
    settings = get_settings()
    parser = argparse.ArgumentParser(description="初始化/提升超级管理员账号（幂等）")
    parser.add_argument("--phone", default=settings.ADMIN_PHONE, help="管理员手机号")
    parser.add_argument("--password", default=settings.ADMIN_PASSWORD or None, help="初始密码（仅新建时需要）")
    parser.add_argument("--nickname", default=settings.ADMIN_NICKNAME, help="昵称")
    args = parser.parse_args()

    init_admin(phone=args.phone, password=args.password, nickname=args.nickname)


if __name__ == "__main__":
    main()
