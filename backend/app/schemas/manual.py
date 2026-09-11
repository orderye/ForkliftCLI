from datetime import datetime
from pydantic import BaseModel, Field


class ManualListItem(BaseModel):
    id: int
    title: str
    summary: str = ""
    source: str = ""
    category: str = ""
    doc_type: str = "manual"
    file_type: str = "markdown"
    forklift_model_id: int | None = None
    engine_model_id: int | None = None
    chunk_count: int = 0
    page_count: int = 0
    license_type: str = "self_owned"
    commercial_use: bool = False
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ManualDetail(ManualListItem):
    content: str = ""
    copyright_owner: str = ""
    license_expire: datetime | None = None


class ManualChunk(BaseModel):
    id: int
    chunk_index: int
    text: str
    page_number: int | None = None
    section_title: str = ""
    source_locator: str = ""


class ManualListResponse(BaseModel):
    items: list[ManualListItem]
    total: int
    page: int
    page_size: int


class ManualSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=10, ge=1, le=30)
    forklift_model_id: int | None = None
    engine_model_id: int | None = None


class ManualSearchHit(BaseModel):
    document_id: int
    chunk_id: int | None = None
    title: str
    text: str
    score: float
    category: str = ""
    page_number: int | None = None
    section_title: str = ""
    source: str = ""


class ManualSearchResponse(BaseModel):
    hits: list[ManualSearchHit]
    safety_warning: str
