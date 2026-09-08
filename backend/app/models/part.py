from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Part(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    oem_number = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), default="")
    category = Column(String(100), default="")
    specifications = Column(Text, default="")
    compatible_models_json = Column(JSON, default=list)
    image_url = Column(String(500), default="")
    brand = Column(String(100), default="")
    unit = Column(String(20), default="个")
    weight_kg = Column(Float, nullable=True)
    price_reference = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    component = relationship("Component", back_populates="parts")
    alternatives = relationship("PartAlternative", foreign_keys="PartAlternative.part_id", back_populates="part")


class PartOem(Base):
    __tablename__ = "part_oems"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    oem_number = Column(String(100), nullable=False, index=True)
    manufacturer = Column(String(100), default="")
    notes = Column(Text, default="")

    part = relationship("Part")


class PartAlternative(Base):
    __tablename__ = "part_alternatives"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    alternative_part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)
    notes = Column(Text, default="")

    part = relationship("Part", foreign_keys=[part_id], back_populates="alternatives")
    alternative_part = relationship("Part", foreign_keys=[alternative_part_id])
