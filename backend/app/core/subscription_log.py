"""订阅变更审计日志"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.subscription import SubscriptionLog


def log_subscription(
    db: Session,
    user_id: int,
    action: str,
    level_before: str = "",
    level_after: str = "",
    expires_before=None,
    expires_after=None,
    note: str = "",
) -> None:
    """写入一条订阅变更记录"""
    db.add(
        SubscriptionLog(
            user_id=user_id,
            action=action,
            level_before=level_before,
            level_after=level_after,
            expires_before=expires_before,
            expires_after=expires_after,
            note=note,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
