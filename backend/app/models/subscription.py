"""订阅与商业化相关模型

- TrialCard：体验卡（专业/企业用户每月发放，免费用户领取激活 7 天专业版）
- EnterpriseAccount：企业版绑定的子账户
- SubscriptionLog：订阅状态变更审计日志
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from app.core.database import Base


class TrialCard(Base):
    __tablename__ = "trial_cards"

    id = Column(Integer, primary_key=True, index=True)
    owner_uid = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_phone = Column(String(20), default="")
    status = Column(String(10), default="unused")  # unused | used | expired
    expire_at = Column(DateTime, nullable=True)
    claimed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EnterpriseAccount(Base):
    __tablename__ = "enterprise_accounts"

    id = Column(Integer, primary_key=True, index=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("enterprise_id", "user_id", name="uq_enterprise_account"),)


class SubscriptionLog(Base):
    __tablename__ = "subscription_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(20), default="")  # activate | renew | cancel | expire | trial | enterprise_bind | enterprise_unbind
    level_before = Column(String(20), default="")
    level_after = Column(String(20), default="")
    expires_before = Column(DateTime, nullable=True)
    expires_after = Column(DateTime, nullable=True)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
