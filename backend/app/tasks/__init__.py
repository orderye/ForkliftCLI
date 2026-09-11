"""定时任务入口。

体验卡发放与订阅过期均由 account-service 统一管理。
ForkliftCLI 本地仅保留用户投影，不维护 TrialCard/Subscription 状态。
"""
from app.tasks.subscription_tasks import (
    monthly_trial_card_distribution,
    expire_trial_cards,
)

__all__ = [
    "monthly_trial_card_distribution",
    "expire_trial_cards",
]