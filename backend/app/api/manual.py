from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.security import get_current_user
from app.core.rate_limit import check_daily_call
from app.core.vector_store import search_similar
from app.models.ai import KnowledgeChunk, KnowledgeDocument
from app.models.copyright_mixin import license_active_condition
from app.models.user import User
from app.schemas.manual import (
    ManualChunk,
    ManualDetail,
    ManualListItem,
    ManualListResponse,
    ManualSearchHit,
    ManualSearchRequest,
    ManualSearchResponse,
)
from app.services.embedding_service import get_text_embedding

router = APIRouter(prefix="/manuals", tags=["维修手册"])


def _active_query(db: Session):
    return db.query(KnowledgeDocument).filter(
        KnowledgeDocument.doc_type == "manual",
        license_active_condition(KnowledgeDocument.license_expire),
    )


def _to_item(db: Session, doc: KnowledgeDocument) -> ManualListItem:
    count = db.query(func.count(KnowledgeChunk.id)).filter(
        KnowledgeChunk.document_id == doc.id
    ).scalar() or 0
    return ManualListItem(
        id=doc.id,
        title=doc.title,
        summary=doc.summary or (doc.content or "")[:240],
        source=doc.source or "",
        category=doc.category or "",
        doc_type=doc.doc_type,
        file_type=doc.file_type or "markdown",
        forklift_model_id=doc.forklift_model_id,
        engine_model_id=doc.engine_model_id,
        chunk_count=count,
        page_count=doc.page_count or 0,
        license_type=doc.license_type or "self_owned",
        commercial_use=bool(doc.commercial_use),
        created_at=doc.created_at,
    )


@router.get("", response_model=ManualListResponse)
@safe_api
def list_manuals(
    keyword: str | None = None,
    category: str | None = None,
    doc_type: str = Query("manual"),
    forklift_model_id: int | None = None,
    engine_model_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = _active_query(db)
    if doc_type:
        query = query.filter(KnowledgeDocument.doc_type == doc_type)
    if keyword:
        term = f"%{keyword}%"
        query = query.filter(
            or_(KnowledgeDocument.title.ilike(term), KnowledgeDocument.summary.ilike(term))
        )
    if category:
        query = query.filter(KnowledgeDocument.category == category)
    if forklift_model_id is not None:
        query = query.filter(KnowledgeDocument.forklift_model_id == forklift_model_id)
    if engine_model_id is not None:
        query = query.filter(KnowledgeDocument.engine_model_id == engine_model_id)
    total = query.count()
    docs = query.order_by(KnowledgeDocument.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return ManualListResponse(
        items=[_to_item(db, doc) for doc in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/model/{model_id}", response_model=ManualListResponse)
@safe_api
def get_model_manuals(
    model_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = _active_query(db).filter(KnowledgeDocument.forklift_model_id == model_id)
    total = query.count()
    docs = query.order_by(KnowledgeDocument.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return ManualListResponse(
        items=[_to_item(db, doc) for doc in docs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/search", response_model=ManualSearchResponse)
@safe_api
def search_manuals(
    req: ManualSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_daily_call(current_user.id, "manual_search")  # 免费版每日 3 次
    hits = search_similar(
        get_text_embedding(req.query),
        req.top_k,
        req.forklift_model_id,
        req.engine_model_id,
    )
    result = []
    for hit in hits:
        payload = hit.get("payload") or {}
        doc_id = payload.get("doc_id")
        doc = _active_query(db).filter(KnowledgeDocument.id == doc_id).first() if doc_id else None
        if not doc:
            continue
        result.append(ManualSearchHit(
            document_id=doc.id,
            chunk_id=payload.get("chunk_id"),
            title=doc.title,
            text=payload.get("text", ""),
            score=float(hit.get("score", 0)),
            category=doc.category or "",
            page_number=payload.get("page_number"),
            section_title=payload.get("section_title", ""),
            source=doc.source or "",
        ))
    return ManualSearchResponse(
        hits=result,
        safety_warning="维修前请停车、熄火、释放液压压力并固定门架，由具备资质的维修人员操作。",
    )


@router.get("/{manual_id}", response_model=ManualDetail)
@safe_api
def get_manual(
    manual_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    doc = _active_query(db).filter(KnowledgeDocument.id == manual_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="维修手册不存在或已失效")
    item = _to_item(db, doc)
    return ManualDetail(
        **item.model_dump(),
        content=doc.content or "",
        copyright_owner=doc.copyright_owner or "",
        license_expire=doc.license_expire,
    )


@router.get("/{manual_id}/chunks", response_model=list[ManualChunk])
@safe_api
def get_manual_chunks(
    manual_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    doc = _active_query(db).filter(KnowledgeDocument.id == manual_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="维修手册不存在或已失效")
    rows = db.query(KnowledgeChunk).filter(
        KnowledgeChunk.document_id == manual_id
    ).order_by(KnowledgeChunk.chunk_index).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return [ManualChunk(
        id=row.id,
        chunk_index=row.chunk_index,
        text=row.chunk_text,
        page_number=row.page_number,
        section_title=row.section_title or "",
        source_locator=row.source_locator or "",
    ) for row in rows]
