from pydantic import BaseModel, Field, model_validator


_MAX_TEXT_LENGTH = 4_000
_MAX_IMAGE_BASE64_LENGTH = 12_000_000


class EmbedRequest(BaseModel):
    text: str | None = Field(default=None, max_length=_MAX_TEXT_LENGTH)
    image_base64: str | None = Field(default=None, max_length=_MAX_IMAGE_BASE64_LENGTH)

    @model_validator(mode="after")
    def validate_input(self):
        has_text = bool(self.text and self.text.strip())
        has_image = bool(self.image_base64 and self.image_base64.strip())
        if has_text == has_image:
            raise ValueError("text and image_base64 must contain exactly one value")
        return self


class EmbedResponse(BaseModel):
    vector: list[float]


class SearchRequest(BaseModel):
    query_text: str | None = Field(default=None, max_length=_MAX_TEXT_LENGTH)
    query_image_base64: str | None = Field(default=None, max_length=_MAX_IMAGE_BASE64_LENGTH)
    top_k: int = Field(default=5, ge=1, le=50)
    forklift_model_id: int | None = Field(default=None, ge=1)
    engine_model_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_input(self):
        has_text = bool(self.query_text and self.query_text.strip())
        has_image = bool(self.query_image_base64 and self.query_image_base64.strip())
        if has_text == has_image:
            raise ValueError("query_text and query_image_base64 must contain exactly one value")
        return self


class SearchHit(BaseModel):
    id: int | str
    score: float
    payload: dict


class SearchResponse(BaseModel):
    hits: list[SearchHit]