from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base


class User(Base):
    """ForkliftCLI 本地用户投影：仅保留业务关联所需字段，认证/订阅归 account-service。

    ponytail: 本地表不再存密码/权限，避免双库权限漂移；等级来自 account-service 登录返回的投影。
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(255), default="", index=True)
    nickname = Column(String(50), default="")
    avatar = Column(String(500), default="")
    subscription_level = Column(String(20), default="free", index=True)
    subscription_expires_at = Column(DateTime, nullable=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=True)
    device_token = Column(String(500), default="")
    is_active = Column(Boolean, default=True, index=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
