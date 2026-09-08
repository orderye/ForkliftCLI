from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.part import Part, PartAlternative
from app.models.diagram import Diagram, DiagramHotspot
from app.schemas.part import PartOut, PartDetail, PartAltOut, PartSearchResult
from app.schemas.forklift import DiagramOut, HotspotOut

router = APIRouter(prefix="/parts", tags=["配件"])


@router.get("/search", response_model=PartSearchResult)
@safe_api
def search_parts(
    q: str = Query("", description="搜索关键词（OEM编号/名称）"),
    category: str = Query("", description="分类"),
    model_id: int = Query(0, description="车型ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Part)

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            Part.oem_number.ilike(pattern) | Part.name.ilike(pattern)
        )
    if category:
        query = query.filter(Part.category == category)
    if model_id:
        query = query.filter(Part.compatible_models_json.op("@>")(str([model_id])))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PartSearchResult(
        parts=[PartOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{part_id}", response_model=PartDetail)
@safe_api
def get_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(Part).filter(Part.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="配件不存在")

    alts = (
        db.query(PartAlternative)
        .filter(PartAlternative.part_id == part_id)
        .all()
    )
    result = PartDetail.model_validate(part)
    result.alternatives = [PartAltOut.model_validate(a) for a in alts]
    return result


# ========== 结构图 ==========

diagram_router = APIRouter(prefix="/diagrams", tags=["结构图"])


@diagram_router.get("/model/{model_id}", response_model=list[DiagramOut])
@safe_api
def list_model_diagrams(
    model_id: int,
    diagram_type: str = Query("", description="structure | exploded"),
    db: Session = Depends(get_db),
):
    query = db.query(Diagram).filter(Diagram.model_id == model_id)
    if diagram_type:
        query = query.filter(Diagram.diagram_type == diagram_type)
    return query.all()


@diagram_router.get("/engine/{engine_model_id}", response_model=list[DiagramOut])
@safe_api
def list_engine_diagrams(engine_model_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Diagram)
        .filter(Diagram.engine_model_id == engine_model_id)
        .all()
    )


@diagram_router.get("/{diagram_id}/hotspots", response_model=list[HotspotOut])
@safe_api
def list_hotspots(diagram_id: int, db: Session = Depends(get_db)):
    return (
        db.query(DiagramHotspot)
        .filter(DiagramHotspot.diagram_id == diagram_id)
        .all()
    )
