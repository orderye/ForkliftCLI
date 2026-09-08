from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.forklift import (
    ForkliftBrand, ForkliftSeries, ForkliftModel,
    ForkliftSpecification, ForkliftSystem, Component,
)
from app.models.engine import EngineBrand, EngineModel
from app.schemas.forklift import (
    BrandOut, SeriesOut, ModelOut, ModelDetail, SpecificationOut,
    EngineBrandOut, EngineModelOut, EngineModelDetail,
    SystemOut, ComponentOut,
)

router = APIRouter(prefix="/forklifts", tags=["车型库"])


# ========== 品牌 ==========

@router.get("/brands", response_model=list[BrandOut])
@safe_api
def list_brands(db: Session = Depends(get_db)):
    return db.query(ForkliftBrand).order_by(ForkliftBrand.name).all()


# ========== 系列 ==========

@router.get("/brands/{brand_id}/series", response_model=list[SeriesOut])
@safe_api
def list_series(brand_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ForkliftSeries)
        .filter(ForkliftSeries.brand_id == brand_id)
        .order_by(ForkliftSeries.name)
        .all()
    )


# ========== 车型 ==========

@router.get("/series/{series_id}/models", response_model=list[ModelOut])
@safe_api
def list_models(series_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ForkliftModel)
        .filter(ForkliftModel.series_id == series_id)
        .order_by(ForkliftModel.name)
        .all()
    )


@router.get("/models/{model_id}", response_model=ModelDetail)
@safe_api
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(ForkliftModel).filter(ForkliftModel.id == model_id).first()
    if not model:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="车型不存在")

    result = ModelDetail.model_validate(model)
    result.brand_name = model.series.brand.name if model.series else ""
    result.series_name = model.series.name if model.series else ""
    return result


@router.get("/models/{model_id}/specification", response_model=SpecificationOut)
@safe_api
def get_specification(model_id: int, db: Session = Depends(get_db)):
    spec = db.query(ForkliftSpecification).filter(
        ForkliftSpecification.model_id == model_id
    ).first()
    if not spec:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="暂无参数信息")
    return SpecificationOut.model_validate(spec)


@router.get("/models/{model_id}/systems", response_model=list[SystemOut])
@safe_api
def list_systems(model_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ForkliftSystem)
        .filter(ForkliftSystem.model_id == model_id)
        .all()
    )


@router.get("/systems/{system_id}/components", response_model=list[ComponentOut])
@safe_api
def list_components(system_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Component)
        .filter(Component.system_id == system_id)
        .all()
    )


# ========== 搜索 ==========

@router.get("/search")
@safe_api
def search_models(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    pattern = f"%{q}%"
    results = (
        db.query(ForkliftModel)
        .join(ForkliftSeries)
        .join(ForkliftBrand)
        .filter(
            ForkliftModel.name.ilike(pattern)
            | ForkliftSeries.name.ilike(pattern)
            | ForkliftBrand.name.ilike(pattern)
        )
        .limit(20)
        .all()
    )
    return [
        {
            "id": m.id,
            "name": m.name,
            "brand": m.series.brand.name,
            "series": m.series.name,
            "fuel_type": m.fuel_type,
            "load_capacity_kg": m.load_capacity_kg,
        }
        for m in results
    ]


# ========== 发动机 ==========

engine_router = APIRouter(prefix="/engines", tags=["发动机"])


@engine_router.get("/brands", response_model=list[EngineBrandOut])
@safe_api
def list_engine_brands(db: Session = Depends(get_db)):
    return db.query(EngineBrand).order_by(EngineBrand.name).all()


@engine_router.get("/brands/{brand_id}/models", response_model=list[EngineModelOut])
@safe_api
def list_engine_models(brand_id: int, db: Session = Depends(get_db)):
    return (
        db.query(EngineModel)
        .filter(EngineModel.brand_id == brand_id)
        .order_by(EngineModel.model_name)
        .all()
    )


@engine_router.get("/models/{model_id}", response_model=EngineModelDetail)
@safe_api
def get_engine_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(EngineModel).filter(EngineModel.id == model_id).first()
    if not model:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="发动机型号不存在")
    result = EngineModelDetail.model_validate(model)
    result.brand_name = model.brand.name if model.brand else ""
    return result


@engine_router.get("/search")
@safe_api
def search_engines(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    pattern = f"%{q}%"
    results = (
        db.query(EngineModel)
        .join(EngineBrand)
        .filter(
            EngineModel.model_name.ilike(pattern)
            | EngineBrand.name.ilike(pattern)
        )
        .limit(20)
        .all()
    )
    return [
        {
            "id": m.id,
            "brand": m.brand.name,
            "model_name": m.model_name,
            "displacement": m.displacement,
            "power_kw": m.power_kw,
        }
        for m in results
    ]
