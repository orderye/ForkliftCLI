from pydantic import BaseModel


class BrandOut(BaseModel):
    id: int
    name: str
    name_en: str
    logo: str
    country: str

    class Config:
        from_attributes = True


class SeriesOut(BaseModel):
    id: int
    brand_id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class ModelOut(BaseModel):
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
    fuel_type: str
    image_url: str

    class Config:
        from_attributes = True


class ModelDetail(BaseModel):
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
    wheelbase_mm: float | None = None
    turning_radius_mm: float | None = None
    max_speed_kmh: float | None = None
    fuel_type: str
    image_url: str
    brand_name: str = ""
    series_name: str = ""

    class Config:
        from_attributes = True


class SpecificationOut(BaseModel):
    engine_type: str
    engine_displacement: str
    engine_power_kw: float | None = None
    transmission_type: str
    hydraulic_system: str
    brake_type: str
    steering_type: str
    tire_spec: str
    battery_voltage: str

    class Config:
        from_attributes = True


class EngineBrandOut(BaseModel):
    id: int
    name: str
    name_en: str
    country: str

    class Config:
        from_attributes = True


class EngineModelOut(BaseModel):
    id: int
    brand_id: int
    model_name: str
    displacement: str
    power_kw: float | None = None
    power_hp: float | None = None
    cylinders: int | None = None
    fuel_type: str

    class Config:
        from_attributes = True


class EngineModelDetail(BaseModel):
    id: int
    brand_id: int
    model_name: str
    displacement: str
    power_kw: float | None = None
    power_hp: float | None = None
    cylinders: int | None = None
    fuel_type: str
    aspiration: str
    emission_standard: str
    weight_kg: float | None = None
    description: str
    brand_name: str = ""

    class Config:
        from_attributes = True


class DiagramOut(BaseModel):
    id: int
    model_id: int | None = None
    diagram_type: str
    system_type: str
    title: str
    image_url: str

    class Config:
        from_attributes = True


class HotspotOut(BaseModel):
    id: int
    component_id: int | None = None
    part_id: int | None = None
    label: str
    x: int
    y: int
    width: int
    height: int

    class Config:
        from_attributes = True


class ComponentOut(BaseModel):
    id: int
    system_id: int
    name: str
    part_number: str

    class Config:
        from_attributes = True


class SystemOut(BaseModel):
    id: int
    model_id: int
    system_type: str
    name: str

    class Config:
        from_attributes = True
