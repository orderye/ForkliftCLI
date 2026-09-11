"""知识库管理 API（与后台管理模块分离，便于独立扩展）

功能：knowledge_documents 的 CRUD 操作，含分块查询
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.admin.common import client_ip, paginate, snapshot, write_audit
from app.core.admin_auth import require_admin
from app.core.database import get_db
from app.models.ai import KnowledgeDocument, KnowledgeChunk
from app.models.user import User
from app.schemas.admin import (
    KnowledgeDocCreate,
    KnowledgeDocOut,
    KnowledgeDocUpdate,
    PageOut,
)

router = APIRouter(prefix="/knowledge", tags=["知识库管理"])

VALID_DOC_TYPES = {"manual", "fault", "case", "parameter"}


@router.get("/documents", response_model=PageOut[KnowledgeDocOut])
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    doc_type: Optional[str] = None,
    forklift_model_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(KnowledgeDocument)
    if doc_type:
        query = query.filter(KnowledgeDocument.doc_type == doc_type)
    if forklift_model_id:
        query = query.filter(KnowledgeDocument.forklift_model_id == forklift_model_id)
    if keyword:
        query = query.filter(
            (KnowledgeDocument.title.ilike(f"%{keyword}%"))
            | (KnowledgeDocument.content.ilike(f"%{keyword}%"))
        )
    return paginate(query.order_by(KnowledgeDocument.id.desc()), page, page_size)


@router.get("/documents/{doc_id}", response_model=KnowledgeDocOut)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@router.post("/documents", response_model=KnowledgeDocOut)
def create_document(
    data: KnowledgeDocCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if data.doc_type not in VALID_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"非法文档类型：{data.doc_type}")
    doc = KnowledgeDocument(**data.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    write_audit(
        db,
        admin_id=admin.id,
        action="create",
        target_type="knowledge_document",
        target_id=doc.id,
        after=snapshot(doc),
        ip=client_ip(request),
    )
    return doc


@router.put("/documents/{doc_id}", response_model=KnowledgeDocOut)
def update_document(
    doc_id: int,
    data: KnowledgeDocUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    fields = data.model_dump(exclude_unset=True)
    if fields.get("doc_type") is not None and fields["doc_type"] not in VALID_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"非法文档类型：{fields['doc_type']}")

    before = snapshot(doc)
    for key, value in fields.items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    write_audit(
        db,
        admin_id=admin.id,
        action="update",
        target_type="knowledge_document",
        target_id=doc.id,
        before=before,
        after=snapshot(doc),
        ip=client_ip(request),
    )
    return doc


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    before = snapshot(doc)
    # 同步清理分块
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc_id).delete()
    db.delete(doc)
    db.commit()
    write_audit(
        db,
        admin_id=admin.id,
        action="delete",
        target_type="knowledge_document",
        target_id=doc_id,
        before=before,
        ip=client_ip(request),
    )
    return {"message": "文档已删除（含分块）"}


@router.get("/documents/{doc_id}/chunks", response_model=List[dict])
def list_chunks(
    doc_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.document_id == doc_id)
        .order_by(KnowledgeChunk.chunk_index.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [
        {
            "id": c.id,
            "index": c.chunk_index,
            "text": c.chunk_text,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in chunks
    ]