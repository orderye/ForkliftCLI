from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from app.core.database import Base


class AdminAuditLogs(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    # 可空：account-service 侧的管理员没有本地 users 投影，审计记录不能因缺少外键而写不进去
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)  # create/update/delete/export/import
    target_type = Column(String(50), nullable=False)  # user/enterprise/forklift/etc.
    target_id = Column(Integer, nullable=True)  # 关联表的ID，可能为空（如批量操作）
    before_json = Column(JSON, nullable=True)  # 操作前数据快照
    after_json = Column(JSON, nullable=True)   # 操作后数据快照
    ip = Column(String(45), default="")  # 操作IP
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))