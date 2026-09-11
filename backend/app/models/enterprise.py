from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Enterprise(Base):
    __tablename__ = "enterprises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    contact_name = Column(String(50), default="")
    contact_phone = Column(String(20), default="")
    address = Column(String(255), default="")
    plan = Column(String(20), default="free")  # free | pro | enterprise
    plan_expire_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active | disabled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", backref="enterprise_obj")
