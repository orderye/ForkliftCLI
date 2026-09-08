from pydantic import BaseModel


class PartOut(BaseModel):
    id: int
    oem_number: str
    name: str
    name_en: str
    category: str
    specifications: str
    compatible_models_json: list
    image_url: str
    brand: str
    unit: str
    price_reference: float | None = None

    class Config:
        from_attributes = True


class PartDetail(PartOut):
    component_id: int | None = None
    weight_kg: float | None = None
    alternatives: list["PartAltOut"] = []


class PartAltOut(BaseModel):
    id: int
    alternative_part_id: int
    notes: str

    class Config:
        from_attributes = True


class PartSearchResult(BaseModel):
    parts: list[PartOut]
    total: int
    page: int
    page_size: int
