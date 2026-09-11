"""后台管理系统 Pydantic 模型（请求/响应）"""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageOut(BaseModel, Generic[T]):
    """统一分页响应"""
    items: list[T]
    total: int
    page: int
    page_size: int


# ========== 版权合规字段（4.3） ==========

class CopyrightFields(BaseModel):
    """创建用：版权合规字段（不含 source，由各 Schema 自行定义）"""
    copyright_owner: str = ""
    license_type: str = "self_owned"
    license_expire: datetime | None = None
    commercial_use: bool = False


class CopyrightFieldsUpdate(BaseModel):
    """更新用：版权合规字段（仅传入的字段生效）"""
    copyright_owner: str | None = None
    license_type: str | None = None
    license_expire: datetime | None = None
    commercial_use: bool | None = None


class CopyrightFieldsOut(BaseModel):
    """输出用：版权合规字段"""
    copyright_owner: str = ""
    license_type: str = "self_owned"
    license_expire: datetime | None = None
    commercial_use: bool = False


# ========== 用户 ==========

class AdminUserOut(BaseModel):
    id: int
    phone: str | None = None
    email: str | None = None
    nickname: str = ""
    avatar: str = ""
    role: str = "user"
    enterprise_id: int | None = None
    enterprise_name: str = ""
    status: str = "active"
    last_login_at: datetime | None = None
    is_super_admin: bool = False
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    nickname: str | None = None
    role: str | None = None          # user | technician | operator | admin
    status: str | None = None        # active | disabled
    enterprise_id: int | None = None
    is_super_admin: bool | None = None  # 仅超级管理员可改


# ========== 企业 ==========

class EnterpriseCreate(BaseModel):
    name: str
    code: str
    contact_name: str = ""
    contact_phone: str = ""
    address: str = ""
    plan: str = "free"               # free | pro | enterprise
    plan_expire_at: datetime | None = None
    status: str = "active"


class EnterpriseUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    plan: str | None = None
    plan_expire_at: datetime | None = None
    status: str | None = None


class EnterpriseOut(BaseModel):
    id: int
    name: str
    code: str
    contact_name: str = ""
    contact_phone: str = ""
    address: str = ""
    plan: str = "free"
    plan_expire_at: datetime | None = None
    status: str = "active"
    created_at: datetime | None = None
    user_count: int = 0

    class Config:
        from_attributes = True


# ========== 车型目录 ==========

class BrandCreate(BaseModel):
    name: str
    name_en: str = ""
    logo: str = ""
    country: str = ""


class BrandUpdate(BaseModel):
    name: str | None = None
    name_en: str | None = None
    logo: str | None = None
    country: str | None = None


class BrandOut(BaseModel):
    id: int
    name: str
    name_en: str = ""
    logo: str = ""
    country: str = ""
    series_count: int = 0

    class Config:
        from_attributes = True


class SeriesCreate(BaseModel):
    brand_id: int
    name: str
    description: str = ""


class SeriesUpdate(BaseModel):
    brand_id: int | None = None
    name: str | None = None
    description: str | None = None


class SeriesOut(BaseModel):
    id: int
    brand_id: int
    name: str
    description: str = ""
    brand_name: str = ""
    model_count: int = 0

    class Config:
        from_attributes = True


class ForkliftModelCreate(BaseModel):
    series_id: int
    name: str
    year_start: int | None = None
    year_end: int | None = None
    load_capacity_kg: float | None = None
    load_capacity_ton: float | None = None
    lift_height_mm: float | None = None
    weight_kg: float | None = None
    length_mm: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    wheelbase_mm: float | None = None
    turning_radius_mm: float | None = None
    max_speed_kmh: float | None = None
    fuel_type: str = ""
    engine_model_id: int | None = None
    image_url: str = ""


class ForkliftModelUpdate(BaseModel):
    series_id: int | None = None
    name: str | None = None
    year_start: int | None = None
    year_end: int | None = None
    load_capacity_kg: float | None = None
    load_capacity_ton: float | None = None
    lift_height_mm: float | None = None
    weight_kg: float | None = None
    length_mm: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    wheelbase_mm: float | None = None
    turning_radius_mm: float | None = None
    max_speed_kmh: float | None = None
    fuel_type: str | None = None
    engine_model_id: int | None = None
    image_url: str | None = None


class ForkliftModelOut(BaseModel):
    id: int
    series_id: int
    name: str
    year_start: int | None = None
    year_end: int | None = None
    load_capacity_kg: float | None = None
    load_capacity_ton: float | None = None
    lift_height_mm: float | None = None
    weight_kg: float | None = None
    length_mm: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    fuel_type: str = ""
    engine_model_id: int | None = None
    image_url: str = ""
    series_name: str = ""

    class Config:
        from_attributes = True


class EngineBrandCreate(BaseModel):
    name: str
    name_en: str = ""
    country: str = ""


class EngineBrandUpdate(BaseModel):
    name: str | None = None
    name_en: str | None = None
    country: str | None = None


class EngineBrandOut(BaseModel):
    id: int
    name: str
    name_en: str = ""
    country: str = ""
    model_count: int = 0

    class Config:
        from_attributes = True


class EngineModelCreate(BaseModel):
    brand_id: int
    model_name: str
    displacement: str = ""
    power_kw: float | None = None
    power_hp: float | None = None
    cylinders: int | None = None
    fuel_type: str = ""
    aspiration: str = ""
    emission_standard: str = ""
    weight_kg: float | None = None
    description: str = ""


class EngineModelUpdate(BaseModel):
    brand_id: int | None = None
    model_name: str | None = None
    displacement: str | None = None
    power_kw: float | None = None
    power_hp: float | None = None
    cylinders: int | None = None
    fuel_type: str | None = None
    aspiration: str | None = None
    emission_standard: str | None = None
    weight_kg: float | None = None
    description: str | None = None


class EngineModelOut(BaseModel):
    id: int
    brand_id: int
    model_name: str
    displacement: str = ""
    power_kw: float | None = None
    power_hp: float | None = None
    cylinders: int | None = None
    fuel_type: str = ""
    aspiration: str = ""
    emission_standard: str = ""
    weight_kg: float | None = None
    description: str = ""
    brand_name: str = ""

    class Config:
        from_attributes = True


class PartCreate(BaseModel):
    component_id: int | None = None
    oem_number: str
    name: str
    name_en: str = ""
    category: str = ""
    specifications: str = ""
    image_url: str = ""
    brand: str = ""
    unit: str = "个"
    weight_kg: float | None = None
    price_reference: float | None = None


class PartUpdate(BaseModel):
    component_id: int | None = None
    oem_number: str | None = None
    name: str | None = None
    name_en: str | None = None
    category: str | None = None
    specifications: str | None = None
    image_url: str | None = None
    brand: str | None = None
    unit: str | None = None
    weight_kg: float | None = None
    price_reference: float | None = None


class PartOut(BaseModel):
    id: int
    component_id: int | None = None
    oem_number: str
    name: str
    name_en: str = ""
    category: str = ""
    specifications: str = ""
    image_url: str = ""
    brand: str = ""
    unit: str = "个"
    weight_kg: float | None = None
    price_reference: float | None = None

    class Config:
        from_attributes = True


# ========== 资产（结构图/3D模型） ==========

class DiagramCreate(CopyrightFields):
    model_id: int | None = None
    engine_model_id: int | None = None
    diagram_type: str                  # structure | exploded | engine
    system_type: str = ""
    title: str = ""
    image_url: str
    thumbnail_url: str = ""
    source: str = ""


class DiagramUpdate(CopyrightFieldsUpdate):
    model_id: int | None = None
    engine_model_id: int | None = None
    diagram_type: str | None = None
    system_type: str | None = None
    title: str | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    source: str | None = None


class DiagramOut(CopyrightFieldsOut):
    id: int
    model_id: int | None = None
    engine_model_id: int | None = None
    diagram_type: str
    system_type: str = ""
    title: str = ""
    image_url: str
    thumbnail_url: str = ""
    source: str = ""
    hotspot_count: int = 0

    class Config:
        from_attributes = True


class Model3DUpdate(CopyrightFieldsUpdate):
    forklift_model_id: int | None = None
    name: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    source: str | None = None
    status: str | None = None          # ready | processing | error


class Model3DOut(CopyrightFieldsOut):
    id: int
    forklift_model_id: int | None = None
    name: str
    description: str = ""
    file_url: str
    thumbnail_url: str = ""
    source: str = ""
    file_size_mb: float = 0
    format: str = "glb"
    version: int = 1
    status: str = "ready"
    uploaded_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ========== 知识库 / 故障数据 ==========

class KnowledgeDocCreate(CopyrightFields):
    title: str
    content: str = ""
    source: str = ""
    doc_type: str = "manual"           # manual | fault | case | parameter
    forklift_model_id: int | None = None
    engine_model_id: int | None = None


class KnowledgeDocUpdate(CopyrightFieldsUpdate):
    title: str | None = None
    content: str | None = None
    source: str | None = None
    doc_type: str | None = None
    forklift_model_id: int | None = None
    engine_model_id: int | None = None


class KnowledgeDocOut(CopyrightFieldsOut):
    id: int
    title: str
    content: str = ""
    source: str = ""
    doc_type: str = "manual"
    forklift_model_id: int | None = None
    engine_model_id: int | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class FaultCodeCreate(BaseModel):
    code: str
    description: str
    severity: str = "medium"           # low | medium | high | critical
    category: str = ""


class FaultCodeUpdate(BaseModel):
    code: str | None = None
    description: str | None = None
    severity: str | None = None
    category: str | None = None


class FaultCodeOut(BaseModel):
    id: int
    code: str
    description: str
    severity: str = "medium"
    category: str = ""

    class Config:
        from_attributes = True


class FaultTreeCreate(BaseModel):
    fault_code_id: int | None = None
    forklift_model_id: int | None = None
    engine_model_id: int | None = None
    symptom: str
    causes_json: list = []
    solutions_json: list = []
    probability_json: dict = {}


class FaultTreeUpdate(BaseModel):
    fault_code_id: int | None = None
    forklift_model_id: int | None = None
    engine_model_id: int | None = None
    symptom: str | None = None
    causes_json: list | None = None
    solutions_json: list | None = None
    probability_json: dict | None = None


class FaultTreeOut(BaseModel):
    id: int
    fault_code_id: int | None = None
    forklift_model_id: int | None = None
    engine_model_id: int | None = None
    symptom: str
    causes_json: list = []
    solutions_json: list = []
    probability_json: dict = {}
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ========== 审计日志 ==========

class AuditLogOut(BaseModel):
    id: int
    admin_user_id: int
    action: str
    target_type: str
    target_id: int | None = None
    before_json: dict | list | None = None
    after_json: dict | list | None = None
    ip: str = ""
    created_at: datetime | None = None

    class Config:
        from_attributes = True
