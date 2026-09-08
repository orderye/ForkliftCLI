from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ForkliftBrand(Base):
    __tablename__ = "forklift_brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    name_en = Column(String(100), default="")
    logo = Column(String(500), default="")
    country = Column(String(50), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    series = relationship("ForkliftSeries", back_populates="brand", cascade="all, delete-orphan")


class ForkliftSeries(Base):
    __tablename__ = "forklift_series"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("forklift_brands.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    brand = relationship("ForkliftBrand", back_populates="series")
    models = relationship("ForkliftModel", back_populates="series", cascade="all, delete-orphan")


class ForkliftModel(Base):
    __tablename__ = "forklift_models"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("forklift_series.id"), nullable=False)
    name = Column(String(100), nullable=False)
    year_start = Column(Integer, nullable=True)
    year_end = Column(Integer, nullable=True)
    load_capacity_kg = Column(Float, nullable=True)
    load_capacity_ton = Column(Float, nullable=True)
    lift_height_mm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    length_mm = Column(Float, nullable=True)
    width_mm = Column(Float, nullable=True)
    height_mm = Column(Float, nullable=True)
    wheelbase_mm = Column(Float, nullable=True)
    turning_radius_mm = Column(Float, nullable=True)
    max_speed_kmh = Column(Float, nullable=True)
    fuel_type = Column(String(50), default="")  # diesel | electric | gasoline | lpg
    engine_model_id = Column(Integer, ForeignKey("engine_models.id"), nullable=True)
    image_url = Column(String(500), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    series = relationship("ForkliftSeries", back_populates="models")
    specification = relationship("ForkliftSpecification", back_populates="model", uselist=False, cascade="all, delete-orphan")
    systems = relationship("ForkliftSystem", back_populates="model", cascade="all, delete-orphan")
    diagrams = relationship("Diagram", back_populates="model", cascade="all, delete-orphan")


class ForkliftSpecification(Base):
    __tablename__ = "forklift_specifications"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("forklift_models.id"), unique=True, nullable=False)
    engine_type = Column(String(100), default="")
    engine_displacement = Column(String(50), default="")
    engine_power_kw = Column(Float, nullable=True)
    engine_rpm = Column(Integer, nullable=True)
    transmission_type = Column(String(100), default="")
    hydraulic_system = Column(String(200), default="")
    brake_type = Column(String(100), default="")
    steering_type = Column(String(100), default="")
    tire_spec = Column(String(100), default="")
    battery_voltage = Column(String(50), default="")
    extra_data = Column(JSON, default=dict)

    model = relationship("ForkliftModel", back_populates="specification")


class ForkliftSystem(Base):
    __tablename__ = "forklift_systems"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("forklift_models.id"), nullable=False)
    system_type = Column(String(50), nullable=False)  # engine | transmission | hydraulic | electrical | brake | steering | mast | frame
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")

    model = relationship("ForkliftModel", back_populates="systems")
    components = relationship("Component", back_populates="system", cascade="all, delete-orphan")


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("forklift_systems.id"), nullable=False)
    name = Column(String(200), nullable=False)
    part_number = Column(String(100), default="")
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    description = Column(Text, default="")

    system = relationship("ForkliftSystem", back_populates="components")
    parts = relationship("Part", back_populates="component", cascade="all, delete-orphan")
