"""支付订单模型

Payment：第三方支付平台的订单记录（微信 / 支付宝 / 应用内支付 IAP）。
状态流转：pending -> success / failed / closed
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(String(20), nullable=False)  # pro | enterprise
    platform = Column(String(20), default="wechat")  # ios | android | wechat | alipay
    amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(10), default="pending")  # pending | success | failed | closed
    transaction_id = Column(String(100), default="")
    payment_params = Column(Text, default="")  # 第三方支付参数（JSON 字符串，如预支付订单）
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_params_dict(self) -> dict:
        import json

        if not self.payment_params:
            return {}
        try:
            return json.loads(self.payment_params)
        except (ValueError, TypeError):
            return {}
