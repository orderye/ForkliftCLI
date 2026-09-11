import base64
import re
from io import BytesIO
from PIL import Image
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.embed import EmbedRequest, EmbedResponse, SearchRequest, SearchResponse
from app.services.embedding_service import get_text_embedding, get_image_embedding
from app.core.vector_store import search_similar
from app.core.error_handler import safe_api
from app.core.security import get_current_user
from app.core.database import get_db
from app.core.rate_limit import check_daily_call
from app.models.user import User

router = APIRouter(prefix="/embed", tags=["多模态向量"])

_DATA_URI_RE = re.compile(r"^data:[^;]*;base64,")


def _decode_image(b64: str) -> Image.Image:
    b64 = _DATA_URI_RE.sub("", b64.strip())
    try:
        raw = base64.b64decode(b64)
        return Image.open(BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid image: {e}")


@router.post("", response_model=EmbedResponse)
@safe_api
def embed(
    req: EmbedRequest,
    current_user: User = Depends(get_current_user),
) -> EmbedResponse:
    check_daily_call(current_user.id, "embed")  # 免费版每日 3 次
    if req.text:
        return EmbedResponse(vector=get_text_embedding(req.text))
    if req.image_base64:
        return EmbedResponse(vector=get_image_embedding(_decode_image(req.image_base64)))
    raise HTTPException(status_code=400, detail="text or image_base64 required")


@router.post("/search", response_model=SearchResponse)
@safe_api
def search(
    req: SearchRequest,
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    check_daily_call(current_user.id, "embed_search")
    if req.query_text:
        vec = get_text_embedding(req.query_text)
    elif req.query_image_base64:
        vec = get_image_embedding(_decode_image(req.query_image_base64))
    else:
        raise HTTPException(status_code=400, detail="query_text or query_image_base64 required")

    hits = search_similar(
        vec,
        top_k=req.top_k,
        forklift_model_id=req.forklift_model_id,
        engine_model_id=req.engine_model_id,
    )
    return SearchResponse(hits=hits)
