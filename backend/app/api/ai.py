from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse, DiagnoseRequest, DiagnoseResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI维修助手"])


@router.post("/chat", response_model=ChatResponse)
@safe_api
def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ai = AIService(db)
    result = ai.chat(
        message=data.message,
        forklift_model_id=data.forklift_model_id,
        engine_model_id=data.engine_model_id,
        history=data.history,
    )
    return ChatResponse(**result)


@router.post("/diagnose", response_model=DiagnoseResponse)
@safe_api
def diagnose(
    data: DiagnoseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ai = AIService(db)
    result = ai.diagnose(
        symptom=data.symptom,
        forklift_model_id=data.forklift_model_id,
        engine_model_id=data.engine_model_id,
    )
    return DiagnoseResponse(**result)


@router.post("/ocr/recognize")
@safe_api
async def recognize_nameplate(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    from app.services.ocr_service import OCRService
    ocr = OCRService()
    contents = await file.read()
    result = ocr.recognize_nameplate(contents, file.filename)
    return result
