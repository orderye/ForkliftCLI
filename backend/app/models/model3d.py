from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Model3D(Base):
    """3D叉车模型"""
    __tablename__ = "model_3d"

    id = Column(Integer, primary_key=True, index=True)
    forklift_model_id = Column(Integer, ForeignKey("forklift_models.id"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    file_url = Column(String(500), nullable=False)  # .glb/.gltf文件
    thumbnail_url = Column(String(500), default="")
    file_size_mb = Column(Float, default=0)
    format = Column(String(20), default="glb")  # glb | gltf
    status = Column(String(20), default="ready")  # ready | processing | error
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    parts = relationship("Model3DPart", back_populates="model", cascade="all, delete-orphan")
    animations = relationship("Model3DAnimation", back_populates="model", cascade="all, delete-orphan")


class Model3DPart(Base):
    """3D模型中的零件"""
    __tablename__ = "model_3d_parts"

    id = Column(Integer, primary_key=True, index=True)
    model_3d_id = Column(Integer, ForeignKey("model_3d.id"), nullable=False)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    name = Column(String(200), nullable=False)
    part_number = Column(String(100), default="")
    oem = Column(String(100), default="")
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    position_z = Column(Float, default=0)
    rotation_x = Column(Float, default=0)
    rotation_y = Column(Float, default=0)
    rotation_z = Column(Float, default=0)
    scale = Column(Float, default=1.0)
    material = Column(String(50), default="steel")
    color = Column(String(20), default="#888888")
    mesh_name = Column(String(200), default="")  # glTF中的节点名
    is_interactive = Column(Integer, default=1)  # 是否可点击
    group = Column(String(50), default="body")  # body | mast | fork | engine | transmission | etc.

    model = relationship("Model3D", back_populates="parts")


class Model3DAnimation(Base):
    """3D模型动画"""
    __tablename__ = "model_3d_animations"

    id = Column(Integer, primary_key=True, index=True)
    model_3d_id = Column(Integer, ForeignKey("model_3d.id"), nullable=False)
    name = Column(String(100), nullable=False)  # mast_up | mast_down | tilt_forward | etc.
    display_name = Column(String(100), default="")
    animation_clip = Column(String(200), default="")  # glTF中的动画名
    duration_ms = Column(Integer, default=1000)
    loop = Column(Integer, default=0)

    model = relationship("Model3D", back_populates="animations")


class ArModelConfig(Base):
    """AR模型配置"""
    __tablename__ = "ar_model_config"

    id = Column(Integer, primary_key=True, index=True)
    model_3d_id = Column(Integer, ForeignKey("model_3d.id"), nullable=False)
    forklift_model_id = Column(Integer, ForeignKey("forklift_models.id"), nullable=True)
    real_length_mm = Column(Float, nullable=True)
    real_width_mm = Column(Float, nullable=True)
    real_height_mm = Column(Float, nullable=True)
    real_mast_height_mm = Column(Float, nullable=True)
    real_wheelbase_mm = Column(Float, nullable=True)
    real_turning_radius_mm = Column(Float, nullable=True)
    scale_factor = Column(Float, default=1.0)  # 1:1 = 1.0
    anchor_type = Column(String(50), default="horizontal_plane")
    occlusion = Column(Integer, default=1)
    lighting = Column(Integer, default=1)
    shadow = Column(Integer, default=1)
