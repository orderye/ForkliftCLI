from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserForklift(Base):
    __tablename__ = "user_forklifts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    forklift_model_id = Column(Integer, ForeignKey("forklift_models.id"), nullable=True)
    customer_name = Column(String(200), default="")
    serial_number = Column(String(100), default="")
    product_number = Column(String(100), default="")
    purchase_date = Column(String(20), default="")
    engine_model = Column(String(100), default="")
    current_hours = Column(Float, default=0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    records = relationship("MaintenanceRecord", back_populates="forklift", cascade="all, delete-orphan")
    reminders = relationship("MaintenanceReminder", back_populates="forklift", cascade="all, delete-orphan")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    forklift_id = Column(Integer, ForeignKey("user_forklifts.id"), nullable=False)
    date = Column(String(20), nullable=False)
    fault_description = Column(Text, default="")
    cause = Column(Text, default="")
    parts_replaced_json = Column(JSON, default=list)
    technician = Column(String(100), default="")
    photos_json = Column(JSON, default=list)
    cost = Column(Float, default=0)
    hours_at_repair = Column(Float, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    forklift = relationship("UserForklift", back_populates="records")


class MaintenanceReminder(Base):
    __tablename__ = "maintenance_reminders"

    id = Column(Integer, primary_key=True, index=True)
    forklift_id = Column(Integer, ForeignKey("user_forklifts.id"), nullable=False)
    item_type = Column(String(50), nullable=False)  # engine_oil | hydraulic_oil | gear_oil | air_filter | etc.
    item_name = Column(String(100), default="")
    interval_type = Column(String(20), default="hours")  # hours | days
    interval_value = Column(Float, nullable=False)
    last_date = Column(String(20), default="")
    last_hours = Column(Float, default=0)
    next_date = Column(String(20), default="")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    forklift = relationship("UserForklift", back_populates="reminders")
