"""后台-知识库与故障数据管理（文档/故障代码/故障树）

注：文档上传后的分块与向量化（RAG ingest）由独立流水线处理，
本模块只负责知识库元数据 CRUD；删除文档时同步清理分块。
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.admin.common import client_ip, paginate, safe_like, snapshot, validate_copyright, write_audit
from app.core.admin_auth import require_admin, AdminPrincipal
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.ai import (
    FaultCode,
    FaultTree,
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.schemas.admin import (
    FaultCodeCreate,
    FaultCodeOut,
    FaultCodeUpdate,
    FaultTreeCreate,
    FaultTreeOut,
    FaultTreeUpdate,
    KnowledgeDocCreate,
    KnowledgeDocOut,
    KnowledgeDocUpdate,
    PageOut,
)

router = APIRouter(prefix="/admin/knowledge", tags=["后台-知识库管理"])

VALID_DOC_TYPES = {"manual", "fault", "case", "parameter"}
VALID_SEVERITY = {"low", "medium", "high", "critical"}


# ========== 知识库文档 ==========

@router.get("/documents", response_model=PageOut[KnowledgeDocOut])
@safe_api
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    doc_type: str | None = None,
    forklift_model_id: int | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(KnowledgeDocument)
    if doc_type:
        query = query.filter(KnowledgeDocument.doc_type == doc_type)
    if forklift_model_id:
        query = query.filter(KnowledgeDocument.forklift_model_id == forklift_model_id)
    if keyword:
        query = query.filter(safe_like(KnowledgeDocument.title, keyword.strip()))
    return paginate(query.order_by(KnowledgeDocument.id.desc()), page, page_size)


@router.post("/documents", response_model=KnowledgeDocOut)
@safe_api
def create_document(data: KnowledgeDocCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    if data.doc_type not in VALID_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"非法文档类型：{data.doc_type}")
    # 与结构图一致：创建同样要走版权合规校验（MASTER_PLAN 4.3）
    validate_copyright(data.model_dump(), current=None)
    doc = KnowledgeDocument(**data.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    write_audit(db, admin_id=admin.id, action="create", target_type="knowledge_document",
                target_id=doc.id, after=snapshot(doc), ip=client_ip(request))
    return doc


@router.put("/documents/{doc_id}", response_model=KnowledgeDocOut)
@safe_api
def update_document(doc_id: int, data: KnowledgeDocUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    fields = data.model_dump(exclude_unset=True)
    if fields.get("doc_type") is not None and fields["doc_type"] not in VALID_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"非法文档类型：{fields['doc_type']}")
    validate_copyright(fields, current=doc)

    before = snapshot(doc)
    for key, value in fields.items():
        setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    write_audit(db, admin_id=admin.id, action="update", target_type="knowledge_document",
                target_id=doc.id, before=before, after=snapshot(doc), ip=client_ip(request))
    return doc


@router.delete("/documents/{doc_id}")
@safe_api
def delete_document(doc_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    before = snapshot(doc)
    # 同步清理分块（模型未定义 relationship，显式删除）
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc_id).delete()
    db.delete(doc)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="knowledge_document",
                target_id=doc_id, before=before, ip=client_ip(request))
    return {"message": "文档已删除（含分块）"}


# ========== 故障代码 ==========

@router.get("/fault-codes", response_model=PageOut[FaultCodeOut])
@safe_api
def list_fault_codes(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(FaultCode)
    if category:
        query = query.filter(FaultCode.category == category)
    if keyword:
        query = query.filter(
            (safe_like(FaultCode.code, keyword.strip())) | (safe_like(FaultCode.description, keyword.strip()))
        )
    return paginate(query.order_by(FaultCode.id.desc()), page, page_size)


@router.post("/fault-codes", response_model=FaultCodeOut)
@safe_api
def create_fault_code(data: FaultCodeCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    if data.severity not in VALID_SEVERITY:
        raise HTTPException(status_code=400, detail=f"非法严重级别：{data.severity}")
    if db.query(FaultCode).filter(FaultCode.code == data.code).first():
        raise HTTPException(status_code=400, detail="故障代码已存在")
    code = FaultCode(**data.model_dump())
    db.add(code)
    db.commit()
    db.refresh(code)
    write_audit(db, admin_id=admin.id, action="create", target_type="fault_code",
                target_id=code.id, after=snapshot(code), ip=client_ip(request))
    return code


@router.put("/fault-codes/{code_id}", response_model=FaultCodeOut)
@safe_api
def update_fault_code(code_id: int, data: FaultCodeUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    code = db.query(FaultCode).filter(FaultCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="故障代码不存在")

    fields = data.model_dump(exclude_unset=True)
    if fields.get("severity") is not None and fields["severity"] not in VALID_SEVERITY:
        raise HTTPException(status_code=400, detail=f"非法严重级别：{fields['severity']}")
    if fields.get("code") is not None and fields["code"] != code.code:
        if db.query(FaultCode).filter(FaultCode.code == fields["code"]).first():
            raise HTTPException(status_code=400, detail="故障代码已存在")

    before = snapshot(code)
    for key, value in fields.items():
        setattr(code, key, value)
    db.commit()
    db.refresh(code)
    write_audit(db, admin_id=admin.id, action="update", target_type="fault_code",
                target_id=code.id, before=before, after=snapshot(code), ip=client_ip(request))
    return code


@router.delete("/fault-codes/{code_id}")
@safe_api
def delete_fault_code(code_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    code = db.query(FaultCode).filter(FaultCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="故障代码不存在")
    tree_count = db.query(FaultTree).filter(FaultTree.fault_code_id == code_id).count()
    if tree_count > 0:
        raise HTTPException(status_code=400, detail=f"该故障代码下仍有 {tree_count} 条故障树，无法删除")
    before = snapshot(code)
    db.delete(code)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="fault_code",
                target_id=code_id, before=before, ip=client_ip(request))
    return {"message": "故障代码已删除"}


# ========== 故障树 ==========

@router.get("/fault-trees", response_model=PageOut[FaultTreeOut])
@safe_api
def list_fault_trees(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    forklift_model_id: int | None = None,
    fault_code_id: int | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(FaultTree)
    if forklift_model_id:
        query = query.filter(FaultTree.forklift_model_id == forklift_model_id)
    if fault_code_id:
        query = query.filter(FaultTree.fault_code_id == fault_code_id)
    return paginate(query.order_by(FaultTree.id.desc()), page, page_size)


@router.post("/fault-trees", response_model=FaultTreeOut)
@safe_api
def create_fault_tree(data: FaultTreeCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    if data.fault_code_id is not None and not db.query(FaultCode).filter(FaultCode.id == data.fault_code_id).first():
        raise HTTPException(status_code=400, detail="关联故障代码不存在")
    tree = FaultTree(**data.model_dump())
    db.add(tree)
    db.commit()
    db.refresh(tree)
    write_audit(db, admin_id=admin.id, action="create", target_type="fault_tree",
                target_id=tree.id, after=snapshot(tree), ip=client_ip(request))
    return tree


@router.put("/fault-trees/{tree_id}", response_model=FaultTreeOut)
@safe_api
def update_fault_tree(tree_id: int, data: FaultTreeUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    tree = db.query(FaultTree).filter(FaultTree.id == tree_id).first()
    if not tree:
        raise HTTPException(status_code=404, detail="故障树不存在")

    fields = data.model_dump(exclude_unset=True)
    if fields.get("fault_code_id") is not None and not db.query(FaultCode).filter(FaultCode.id == fields["fault_code_id"]).first():
        raise HTTPException(status_code=400, detail="关联故障代码不存在")

    before = snapshot(tree)
    for key, value in fields.items():
        setattr(tree, key, value)
    db.commit()
    db.refresh(tree)
    write_audit(db, admin_id=admin.id, action="update", target_type="fault_tree",
                target_id=tree.id, before=before, after=snapshot(tree), ip=client_ip(request))
    return tree


@router.delete("/fault-trees/{tree_id}")
@safe_api
def delete_fault_tree(tree_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    tree = db.query(FaultTree).filter(FaultTree.id == tree_id).first()
    if not tree:
        raise HTTPException(status_code=404, detail="故障树不存在")
    before = snapshot(tree)
    db.delete(tree)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="fault_tree",
                target_id=tree_id, before=before, ip=client_ip(request))
    return {"message": "故障树已删除"}
