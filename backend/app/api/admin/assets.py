"""后台-资产管理（结构图/3D模型元数据管理；文件上传复用 /3d/upload）"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.admin.common import client_ip, paginate, snapshot, validate_copyright, write_audit
from app.core.admin_auth import require_admin, AdminPrincipal
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.diagram import Diagram, DiagramHotspot
from app.models.engine import EngineModel
from app.models.forklift import ForkliftModel
from app.models.model3d import Model3D
from app.schemas.admin import (
    DiagramCreate,
    DiagramOut,
    DiagramUpdate,
    Model3DOut,
    Model3DUpdate,
    PageOut,
)

router = APIRouter(prefix="/admin/assets", tags=["后台-资产管理"])

VALID_DIAGRAM_TYPES = {"structure", "exploded", "engine"}
VALID_MODEL3D_STATUS = {"ready", "processing", "error"}


# ========== 结构图 ==========

def _fill_diagram_counts(diagrams: list[Diagram], db: Session) -> None:
    ids = [d.id for d in diagrams]
    counts = dict(
        db.query(DiagramHotspot.diagram_id, func.count(DiagramHotspot.id))
        .filter(DiagramHotspot.diagram_id.in_(ids))
        .group_by(DiagramHotspot.diagram_id)
        .all()
    ) if ids else {}
    for d in diagrams:
        d.hotspot_count = counts.get(d.id, 0)


@router.get("/diagrams", response_model=PageOut[DiagramOut])
@safe_api
def list_diagrams(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    diagram_type: str | None = None,
    model_id: int | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(Diagram)
    if diagram_type:
        query = query.filter(Diagram.diagram_type == diagram_type)
    if model_id:
        query = query.filter(Diagram.model_id == model_id)
    result = paginate(query.order_by(Diagram.id.desc()), page, page_size)
    _fill_diagram_counts(result["items"], db)
    return result


@router.post("/diagrams", response_model=DiagramOut)
@safe_api
def create_diagram(data: DiagramCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    if data.diagram_type not in VALID_DIAGRAM_TYPES:
        raise HTTPException(status_code=400, detail=f"非法结构图类型：{data.diagram_type}")
    if data.model_id is not None and not db.query(ForkliftModel).filter(ForkliftModel.id == data.model_id).first():
        raise HTTPException(status_code=400, detail="关联车型不存在")
    if data.engine_model_id is not None and not db.query(EngineModel).filter(EngineModel.id == data.engine_model_id).first():
        raise HTTPException(status_code=400, detail="关联发动机型号不存在")
    # 与 update_diagram 一致：创建同样要走版权合规校验（MASTER_PLAN 4.3）
    validate_copyright(data.model_dump(), current=None)

    diagram = Diagram(**data.model_dump())
    db.add(diagram)
    db.commit()
    db.refresh(diagram)
    write_audit(db, admin_id=admin.id, action="create", target_type="diagram",
                target_id=diagram.id, after=snapshot(diagram), ip=client_ip(request))
    _fill_diagram_counts([diagram], db)
    return diagram


@router.put("/diagrams/{diagram_id}", response_model=DiagramOut)
@safe_api
def update_diagram(diagram_id: int, data: DiagramUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="结构图不存在")

    fields = data.model_dump(exclude_unset=True)
    if fields.get("diagram_type") is not None and fields["diagram_type"] not in VALID_DIAGRAM_TYPES:
        raise HTTPException(status_code=400, detail=f"非法结构图类型：{fields['diagram_type']}")
    validate_copyright(fields, current=diagram)

    before = snapshot(diagram)
    for key, value in fields.items():
        setattr(diagram, key, value)
    db.commit()
    db.refresh(diagram)
    write_audit(db, admin_id=admin.id, action="update", target_type="diagram",
                target_id=diagram.id, before=before, after=snapshot(diagram), ip=client_ip(request))
    _fill_diagram_counts([diagram], db)
    return diagram


@router.delete("/diagrams/{diagram_id}")
@safe_api
def delete_diagram(diagram_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    diagram = db.query(Diagram).filter(Diagram.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="结构图不存在")
    before = snapshot(diagram)
    db.delete(diagram)  # hotspots 经 relationship cascade 删除
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="diagram",
                target_id=diagram_id, before=before, ip=client_ip(request))
    return {"message": "结构图已删除（含热点）"}


# ========== 3D 模型 ==========

@router.get("/models3d", response_model=PageOut[Model3DOut])
@safe_api
def list_models3d(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    forklift_model_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(Model3D)
    if forklift_model_id:
        query = query.filter(Model3D.forklift_model_id == forklift_model_id)
    if status:
        query = query.filter(Model3D.status == status)
    return paginate(query.order_by(Model3D.id.desc()), page, page_size)


@router.put("/models3d/{model_id}", response_model=Model3DOut)
@safe_api
def update_model3d(model_id: int, data: Model3DUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    model = db.query(Model3D).filter(Model3D.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="3D模型不存在")

    fields = data.model_dump(exclude_unset=True)
    if fields.get("status") is not None and fields["status"] not in VALID_MODEL3D_STATUS:
        raise HTTPException(status_code=400, detail=f"非法状态：{fields['status']}")
    if fields.get("forklift_model_id") is not None and not db.query(ForkliftModel).filter(ForkliftModel.id == fields["forklift_model_id"]).first():
        raise HTTPException(status_code=400, detail="关联车型不存在")
    validate_copyright(fields, current=model)

    before = snapshot(model)
    for key, value in fields.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    write_audit(db, admin_id=admin.id, action="update", target_type="model3d",
                target_id=model.id, before=before, after=snapshot(model), ip=client_ip(request))
    return model


@router.delete("/models3d/{model_id}")
@safe_api
def delete_model3d(model_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    model = db.query(Model3D).filter(Model3D.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="3D模型不存在")
    before = snapshot(model)
    db.delete(model)  # parts/animations 经 relationship cascade 删除
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="model3d",
                target_id=model_id, before=before, ip=client_ip(request))
    return {"message": "3D模型已删除（含零件与动画）"}
