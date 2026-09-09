from datetime import datetime
from pydantic import BaseModel


class Model3DOut(BaseModel):
    id: int
    forklift_model_id: int | None = None
    name: str
    description: str
    file_url: str
    thumbnail_url: str
    file_size_mb: float
    format: str
    status: str
    version: int = 1
    content_hash: str | None = None
    storage_provider: str | None = None
    storage_key: str | None = None
    mime_type: str | None = None
    uploaded_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class Model3DPartOut(BaseModel):
    id: int
    name: str
    part_number: str
    oem: str
    position_x: float
    position_y: float
    position_z: float
    rotation_x: float
    rotation_y: float
    rotation_z: float
    scale: float
    material: str
    color: str
    mesh_name: str
    is_interactive: int
    group: str
    part_id: int | None = None
    component_id: int | None = None

    class Config:
        from_attributes = True


class Model3DAnimationOut(BaseModel):
    id: int
    name: str
    display_name: str
    animation_clip: str
    duration_ms: int
    loop: int

    class Config:
        from_attributes = True


class ArConfigOut(BaseModel):
    id: int
    model_3d_id: int
    forklift_model_id: int | None = None
    real_length_mm: float | None = None
    real_width_mm: float | None = None
    real_height_mm: float | None = None
    real_mast_height_mm: float | None = None
    real_wheelbase_mm: float | None = None
    real_turning_radius_mm: float | None = None
    scale_factor: float
    anchor_type: str
    occlusion: int
    lighting: int
    shadow: int

    class Config:
        from_attributes = True


class Model3DCreate(BaseModel):
    forklift_model_id: int | None = None
    name: str
    description: str = ""
    format: str = "glb"
