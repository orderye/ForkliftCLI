from pydantic import BaseModel


class EmbedRequest(BaseModel):
    text: str | None = None
    image_base64: str | None = None


class EmbedResponse(BaseModel):
    vector: list[float]


class SearchRequest(BaseModel):
    query_text: str | None = None
    query_image_base64: str | None = None
    top_k: int = 5


class SearchHit(BaseModel):
    id: int | str
    score: float
    payload: dict


class SearchResponse(BaseModel):
    hits: list[SearchHit]