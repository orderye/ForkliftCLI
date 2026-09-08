from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    message: str
    forklift_model_id: int | None = None
    engine_model_id: int | None = None
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []
    suggestions: list[str] = []


class DiagnoseRequest(BaseModel):
    symptom: str
    forklift_model_id: int | None = None
    engine_model_id: int | None = None
    image_url: str | None = None


class DiagnoseResponse(BaseModel):
    possible_causes: list[dict]
    check_order: list[str]
    safety_warnings: list[str]
    references: list[str]
