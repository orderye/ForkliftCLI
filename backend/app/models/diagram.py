from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Diagram(Base):
    __tablename__ = "diagrams"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("forklift_models.id"), nullable=True)
    engine_model_id = Column(Integer, ForeignKey("engine_models.id"), nullable=True)
    diagram_type = Column(String(50), nullable=False)  # structure | exploded | engine
    system_type = Column(String(50), default="")  # engine | transmission | hydraulic | etc.
    title = Column(String(200), default="")
    image_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), default="")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    model = relationship("ForkliftModel", back_populates="diagrams")
    hotspots = relationship("DiagramHotspot", back_populates="diagram", cascade="all, delete-orphan")


class DiagramHotspot(Base):
    __tablename__ = "diagram_hotspots"

    id = Column(Integer, primary_key=True, index=True)
    diagram_id = Column(Integer, ForeignKey("diagrams.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=True)
    label = Column(String(200), default="")
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    width = Column(Integer, default=40)
    height = Column(Integer, default=40)

    diagram = relationship("Diagram", back_populates="hotspots")
