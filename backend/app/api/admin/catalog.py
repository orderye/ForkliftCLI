"""后台-目录管理（品牌/系列/车型/发动机品牌/发动机型号/配件）"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.admin.common import client_ip, paginate, safe_like, snapshot, write_audit
from app.core.admin_auth import require_admin, AdminPrincipal
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.ai import FaultTree, KnowledgeDocument
from app.models.diagram import Diagram, DiagramHotspot
from app.models.engine import EngineBrand, EngineModel
from app.models.forklift import (
    Component,
    ForkliftBrand,
    ForkliftModel,
    ForkliftSeries,
)
from app.models.maintenance import UserForklift
from app.models.model3d import Model3D, Model3DPart
from app.models.part import Part, PartAlternative, PartOem
from app.schemas.admin import (
    BrandCreate,
    BrandOut,
    BrandUpdate,
    EngineBrandCreate,
    EngineBrandOut,
    EngineBrandUpdate,
    EngineModelCreate,
    EngineModelOut,
    EngineModelUpdate,
    ForkliftModelCreate,
    ForkliftModelOut,
    ForkliftModelUpdate,
    PageOut,
    PartCreate,
    PartOut,
    PartUpdate,
    SeriesCreate,
    SeriesOut,
    SeriesUpdate,
)

router = APIRouter(prefix="/admin/catalog", tags=["后台-目录管理"])


def _get_or_404(db: Session, model, obj_id: int, name: str):
    obj = db.query(model).filter(model.id == obj_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{name}不存在")
    return obj


# ========== 叉车品牌 ==========

def _fill_brand_counts(db: Session, brands: list[ForkliftBrand]) -> None:
    ids = [b.id for b in brands]
    counts = dict(
        db.query(ForkliftSeries.brand_id, func.count(ForkliftSeries.id))
        .filter(ForkliftSeries.brand_id.in_(ids))
        .group_by(ForkliftSeries.brand_id)
        .all()
    ) if ids else {}
    for b in brands:
        b.series_count = counts.get(b.id, 0)


@router.get("/brands", response_model=PageOut[BrandOut])
@safe_api
def list_brands(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(ForkliftBrand)
    if keyword:
        query = query.filter(safe_like(func.lower(ForkliftBrand.name), keyword.strip()))
    result = paginate(query.order_by(ForkliftBrand.id.asc()), page, page_size)
    _fill_brand_counts(db, result["items"])
    return result


@router.post("/brands", response_model=BrandOut)
@safe_api
def create_brand(data: BrandCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    if db.query(ForkliftBrand).filter(ForkliftBrand.name == data.name).first():
        raise HTTPException(status_code=400, detail="品牌名已存在")
    brand = ForkliftBrand(**data.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    write_audit(db, admin_id=admin.id, action="create", target_type="forklift_brand",
                target_id=brand.id, after=snapshot(brand), ip=client_ip(request))
    _fill_brand_counts(db, [brand])
    return brand


@router.put("/brands/{brand_id}", response_model=BrandOut)
@safe_api
def update_brand(brand_id: int, data: BrandUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    brand = _get_or_404(db, ForkliftBrand, brand_id, "品牌")
    before = snapshot(brand)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(brand, key, value)
    db.commit()
    db.refresh(brand)
    write_audit(db, admin_id=admin.id, action="update", target_type="forklift_brand",
                target_id=brand.id, before=before, after=snapshot(brand), ip=client_ip(request))
    _fill_brand_counts(db, [brand])
    return brand


@router.delete("/brands/{brand_id}")
@safe_api
def delete_brand(brand_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    brand = _get_or_404(db, ForkliftBrand, brand_id, "品牌")
    series_count = db.query(ForkliftSeries).filter(ForkliftSeries.brand_id == brand_id).count()
    if series_count > 0:
        raise HTTPException(status_code=400, detail=f"该品牌下仍有 {series_count} 个系列，无法删除")
    before = snapshot(brand)
    db.delete(brand)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="forklift_brand",
                target_id=brand_id, before=before, ip=client_ip(request))
    return {"message": "品牌已删除"}


# ========== 叉车系列 ==========

def _fill_series_info(db: Session, series_list: list[ForkliftSeries]) -> None:
    ids = [s.id for s in series_list]
    brand_names = dict(db.query(ForkliftBrand.id, ForkliftBrand.name).all())
    counts = dict(
        db.query(ForkliftModel.series_id, func.count(ForkliftModel.id))
        .filter(ForkliftModel.series_id.in_(ids))
        .group_by(ForkliftModel.series_id)
        .all()
    ) if ids else {}
    for s in series_list:
        s.brand_name = brand_names.get(s.brand_id, "")
        s.model_count = counts.get(s.id, 0)


@router.get("/series", response_model=PageOut[SeriesOut])
@safe_api
def list_series(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    brand_id: int | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(ForkliftSeries)
    if brand_id:
        query = query.filter(ForkliftSeries.brand_id == brand_id)
    result = paginate(query.order_by(ForkliftSeries.id.asc()), page, page_size)
    _fill_series_info(db, result["items"])
    return result


@router.post("/series", response_model=SeriesOut)
@safe_api
def create_series(data: SeriesCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    _get_or_404(db, ForkliftBrand, data.brand_id, "品牌")
    series = ForkliftSeries(**data.model_dump())
    db.add(series)
    db.commit()
    db.refresh(series)
    write_audit(db, admin_id=admin.id, action="create", target_type="forklift_series",
                target_id=series.id, after=snapshot(series), ip=client_ip(request))
    _fill_series_info(db, [series])
    return series


@router.put("/series/{series_id}", response_model=SeriesOut)
@safe_api
def update_series(series_id: int, data: SeriesUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    series = _get_or_404(db, ForkliftSeries, series_id, "系列")
    fields = data.model_dump(exclude_unset=True)
    if fields.get("brand_id") is not None:
        _get_or_404(db, ForkliftBrand, fields["brand_id"], "品牌")
    before = snapshot(series)
    for key, value in fields.items():
        setattr(series, key, value)
    db.commit()
    db.refresh(series)
    write_audit(db, admin_id=admin.id, action="update", target_type="forklift_series",
                target_id=series.id, before=before, after=snapshot(series), ip=client_ip(request))
    _fill_series_info(db, [series])
    return series


@router.delete("/series/{series_id}")
@safe_api
def delete_series(series_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    series = _get_or_404(db, ForkliftSeries, series_id, "系列")
    model_count = db.query(ForkliftModel).filter(ForkliftModel.series_id == series_id).count()
    if model_count > 0:
        raise HTTPException(status_code=400, detail=f"该系列下仍有 {model_count} 个车型，无法删除")
    before = snapshot(series)
    db.delete(series)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="forklift_series",
                target_id=series_id, before=before, ip=client_ip(request))
    return {"message": "系列已删除"}


# ========== 叉车型号 ==========

def _fill_model_info(models: list[ForkliftModel], series_names: dict) -> None:
    for m in models:
        m.series_name = series_names.get(m.series_id, "")


@router.get("/models", response_model=PageOut[ForkliftModelOut])
@safe_api
def list_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    series_id: int | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(ForkliftModel)
    if series_id:
        query = query.filter(ForkliftModel.series_id == series_id)
    if keyword:
        query = query.filter(safe_like(func.lower(ForkliftModel.name), keyword.strip()))
    result = paginate(query.order_by(ForkliftModel.id.desc()), page, page_size)
    series_ids = {m.series_id for m in result["items"]}
    series_names = dict(
        db.query(ForkliftSeries.id, ForkliftSeries.name)
        .filter(ForkliftSeries.id.in_(series_ids))
        .all()
    ) if series_ids else {}
    _fill_model_info(result["items"], series_names)
    return result


@router.post("/models", response_model=ForkliftModelOut)
@safe_api
def create_model(data: ForkliftModelCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    _get_or_404(db, ForkliftSeries, data.series_id, "系列")
    if data.engine_model_id is not None:
        _get_or_404(db, EngineModel, data.engine_model_id, "发动机型号")
    model = ForkliftModel(**data.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    write_audit(db, admin_id=admin.id, action="create", target_type="forklift_model",
                target_id=model.id, after=snapshot(model), ip=client_ip(request))
    model.series_name = model.series.name if model.series else ""
    return model


@router.put("/models/{model_id}", response_model=ForkliftModelOut)
@safe_api
def update_model(model_id: int, data: ForkliftModelUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    model = _get_or_404(db, ForkliftModel, model_id, "车型")
    fields = data.model_dump(exclude_unset=True)
    if fields.get("series_id") is not None:
        _get_or_404(db, ForkliftSeries, fields["series_id"], "系列")
    if fields.get("engine_model_id") is not None:
        _get_or_404(db, EngineModel, fields["engine_model_id"], "发动机型号")
    before = snapshot(model)
    for key, value in fields.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    write_audit(db, admin_id=admin.id, action="update", target_type="forklift_model",
                target_id=model.id, before=before, after=snapshot(model), ip=client_ip(request))
    model.series_name = model.series.name if model.series else ""
    return model


@router.delete("/models/{model_id}")
@safe_api
def delete_model(model_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    model = _get_or_404(db, ForkliftModel, model_id, "车型")
    refs = []
    if db.query(Diagram).filter(Diagram.model_id == model_id).count():
        refs.append("结构图")
    if db.query(Model3D).filter(Model3D.forklift_model_id == model_id).count():
        refs.append("3D模型")
    if db.query(KnowledgeDocument).filter(KnowledgeDocument.forklift_model_id == model_id).count():
        refs.append("知识库文档")
    if db.query(FaultTree).filter(FaultTree.forklift_model_id == model_id).count():
        refs.append("故障树")
    if db.query(UserForklift).filter(UserForklift.forklift_model_id == model_id).count():
        refs.append("用户设备档案")
    if refs:
        raise HTTPException(status_code=400, detail=f"该车型仍被以下数据引用：{'、'.join(refs)}，无法删除")
    before = snapshot(model)
    db.delete(model)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="forklift_model",
                target_id=model_id, before=before, ip=client_ip(request))
    return {"message": "车型已删除"}


# ========== 发动机品牌 ==========

def _fill_engine_brand_counts(db: Session, brands: list[EngineBrand]) -> None:
    ids = [b.id for b in brands]
    counts = dict(
        db.query(EngineModel.brand_id, func.count(EngineModel.id))
        .filter(EngineModel.brand_id.in_(ids))
        .group_by(EngineModel.brand_id)
        .all()
    ) if ids else {}
    for b in brands:
        b.model_count = counts.get(b.id, 0)


@router.get("/engine-brands", response_model=PageOut[EngineBrandOut])
@safe_api
def list_engine_brands(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(EngineBrand)
    if keyword:
        query = query.filter(safe_like(func.lower(EngineBrand.name), keyword.strip()))
    result = paginate(query.order_by(EngineBrand.id.asc()), page, page_size)
    _fill_engine_brand_counts(db, result["items"])
    return result


@router.post("/engine-brands", response_model=EngineBrandOut)
@safe_api
def create_engine_brand(data: EngineBrandCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    if db.query(EngineBrand).filter(EngineBrand.name == data.name).first():
        raise HTTPException(status_code=400, detail="发动机品牌名已存在")
    brand = EngineBrand(**data.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    write_audit(db, admin_id=admin.id, action="create", target_type="engine_brand",
                target_id=brand.id, after=snapshot(brand), ip=client_ip(request))
    _fill_engine_brand_counts(db, [brand])
    return brand


@router.put("/engine-brands/{brand_id}", response_model=EngineBrandOut)
@safe_api
def update_engine_brand(brand_id: int, data: EngineBrandUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    brand = _get_or_404(db, EngineBrand, brand_id, "发动机品牌")
    before = snapshot(brand)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(brand, key, value)
    db.commit()
    db.refresh(brand)
    write_audit(db, admin_id=admin.id, action="update", target_type="engine_brand",
                target_id=brand.id, before=before, after=snapshot(brand), ip=client_ip(request))
    _fill_engine_brand_counts(db, [brand])
    return brand


@router.delete("/engine-brands/{brand_id}")
@safe_api
def delete_engine_brand(brand_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    brand = _get_or_404(db, EngineBrand, brand_id, "发动机品牌")
    model_count = db.query(EngineModel).filter(EngineModel.brand_id == brand_id).count()
    if model_count > 0:
        raise HTTPException(status_code=400, detail=f"该品牌下仍有 {model_count} 个发动机型号，无法删除")
    before = snapshot(brand)
    db.delete(brand)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="engine_brand",
                target_id=brand_id, before=before, ip=client_ip(request))
    return {"message": "发动机品牌已删除"}


# ========== 发动机型号 ==========

@router.get("/engine-models", response_model=PageOut[EngineModelOut])
@safe_api
def list_engine_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    brand_id: int | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(EngineModel)
    if brand_id:
        query = query.filter(EngineModel.brand_id == brand_id)
    if keyword:
        query = query.filter(safe_like(func.lower(EngineModel.model_name), keyword.strip()))
    result = paginate(query.order_by(EngineModel.id.desc()), page, page_size)
    brand_names = dict(db.query(EngineBrand.id, EngineBrand.name).all())
    for m in result["items"]:
        m.brand_name = brand_names.get(m.brand_id, "")
    return result


@router.post("/engine-models", response_model=EngineModelOut)
@safe_api
def create_engine_model(data: EngineModelCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    _get_or_404(db, EngineBrand, data.brand_id, "发动机品牌")
    model = EngineModel(**data.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    write_audit(db, admin_id=admin.id, action="create", target_type="engine_model",
                target_id=model.id, after=snapshot(model), ip=client_ip(request))
    model.brand_name = model.brand.name if model.brand else ""
    return model


@router.put("/engine-models/{model_id}", response_model=EngineModelOut)
@safe_api
def update_engine_model(model_id: int, data: EngineModelUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    model = _get_or_404(db, EngineModel, model_id, "发动机型号")
    fields = data.model_dump(exclude_unset=True)
    if fields.get("brand_id") is not None:
        _get_or_404(db, EngineBrand, fields["brand_id"], "发动机品牌")
    before = snapshot(model)
    for key, value in fields.items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    write_audit(db, admin_id=admin.id, action="update", target_type="engine_model",
                target_id=model.id, before=before, after=snapshot(model), ip=client_ip(request))
    model.brand_name = model.brand.name if model.brand else ""
    return model


@router.delete("/engine-models/{model_id}")
@safe_api
def delete_engine_model(model_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    model = _get_or_404(db, EngineModel, model_id, "发动机型号")
    refs = []
    if db.query(ForkliftModel).filter(ForkliftModel.engine_model_id == model_id).count():
        refs.append("叉车型号")
    if db.query(Diagram).filter(Diagram.engine_model_id == model_id).count():
        refs.append("结构图")
    if db.query(KnowledgeDocument).filter(KnowledgeDocument.engine_model_id == model_id).count():
        refs.append("知识库文档")
    if db.query(FaultTree).filter(FaultTree.engine_model_id == model_id).count():
        refs.append("故障树")
    if refs:
        raise HTTPException(status_code=400, detail=f"该发动机型号仍被以下数据引用：{'、'.join(refs)}，无法删除")
    before = snapshot(model)
    db.delete(model)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="engine_model",
                target_id=model_id, before=before, ip=client_ip(request))
    return {"message": "发动机型号已删除"}


# ========== 配件 ==========

@router.get("/parts", response_model=PageOut[PartOut])
@safe_api
def list_parts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str | None = Query(None, description="配件名/OEM号模糊搜索"),
    category: str | None = None,
    db: Session = Depends(get_db),
    _: AdminPrincipal = Depends(require_admin),
):
    query = db.query(Part)
    if category:
        query = query.filter(Part.category == category)
    if keyword:
        query = query.filter(
            or_(
                safe_like(func.lower(Part.name), keyword.strip()),
                safe_like(func.lower(Part.oem_number), keyword.strip()),
            )
        )
    return paginate(query.order_by(Part.id.desc()), page, page_size)


@router.post("/parts", response_model=PartOut)
@safe_api
def create_part(data: PartCreate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    if data.component_id is not None:
        _get_or_404(db, Component, data.component_id, "部件")
    part = Part(**data.model_dump())
    db.add(part)
    db.commit()
    db.refresh(part)
    write_audit(db, admin_id=admin.id, action="create", target_type="part",
                target_id=part.id, after=snapshot(part), ip=client_ip(request))
    return part


@router.put("/parts/{part_id}", response_model=PartOut)
@safe_api
def update_part(part_id: int, data: PartUpdate, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    part = _get_or_404(db, Part, part_id, "配件")
    fields = data.model_dump(exclude_unset=True)
    if fields.get("component_id") is not None:
        _get_or_404(db, Component, fields["component_id"], "部件")
    before = snapshot(part)
    for key, value in fields.items():
        setattr(part, key, value)
    db.commit()
    db.refresh(part)
    write_audit(db, admin_id=admin.id, action="update", target_type="part",
                target_id=part.id, before=before, after=snapshot(part), ip=client_ip(request))
    return part


@router.delete("/parts/{part_id}")
@safe_api
def delete_part(part_id: int, request: Request, db: Session = Depends(get_db), admin: AdminPrincipal = Depends(require_admin)):
    part = _get_or_404(db, Part, part_id, "配件")
    refs = []
    if db.query(PartOem).filter(PartOem.part_id == part_id).count():
        refs.append("OEM编号")
    if db.query(PartAlternative).filter(
        (PartAlternative.part_id == part_id) | (PartAlternative.alternative_part_id == part_id)
    ).count():
        refs.append("替代件关系")
    if db.query(DiagramHotspot).filter(DiagramHotspot.part_id == part_id).count():
        refs.append("结构图热点")
    if db.query(Model3DPart).filter(Model3DPart.part_id == part_id).count():
        refs.append("3D模型零件")
    if refs:
        raise HTTPException(status_code=400, detail=f"该配件仍被以下数据引用：{'、'.join(refs)}，无法删除")
    before = snapshot(part)
    db.delete(part)
    db.commit()
    write_audit(db, admin_id=admin.id, action="delete", target_type="part",
                target_id=part_id, before=before, ip=client_ip(request))
    return {"message": "配件已删除"}
