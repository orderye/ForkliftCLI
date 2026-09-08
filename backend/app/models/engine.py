from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class EngineBrand(Base):
    __tablename__ = "engine_brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    name_en = Column(String(100), default="")
    country = Column(String(50), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    models = relationship("EngineModel", back_populates="brand", cascade="all, delete-orphan")


class EngineModel(Base):
    __tablename__ = "engine_models"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("engine_brands.id"), nullable=False)
    model_name = Column(String(100), nullable=False)
    displacement = Column(String(50), default="")
    power_kw = Column(Float, nullable=True)
    power_hp = Column(Float, nullable=True)
    cylinders = Column(Integer, nullable=True)
    fuel_type = Column(String(50), default="")
    aspiration = Column(String(50), default="")  # naturally aspirated | turbo
    emission_standard = Column(String(50), default="")
    weight_kg = Column(Float, nullable=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    brand = relationship("EngineBrand", back_populates="models")
