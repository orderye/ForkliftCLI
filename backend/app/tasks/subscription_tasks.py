"""订阅相关定时任务（cron）。

体验卡发放与订阅过期均由 account-service 统一管理。
ForkliftCLI 本地仅保留用户投影，不维护 TrialCard/Subscription 状态。
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User


def monthly_trial_card_distribution(db: Session) -> dict:
    """占位实现：体验卡发放由 account-service 负责，此处仅返回空统计。"""
    return {"pro_cards": 0, "enterprise_cards": 0}


def expire_trial_cards(db: Session) -> int:
    """占位实现：体验卡过期清理由 account-service 负责，此处仅返回 0。"""
    return 0