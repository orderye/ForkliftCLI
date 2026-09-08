from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.security import get_current_user
from app.models.user import User
from app.models.model3d import Model3D, Model3DPart, Model3DAnimation, ArModelConfig
from app.schemas.model3d import Model3DOut, Model3DPartOut, Model3DAnimationOut, ArConfigOut
import os

router = APIRouter(prefix="/3d", tags=["3D模型"])


@router.get("/models", response_model=list[Model3DOut])
@safe_api
def list_models(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Model3D).order_by(Model3D.created_at.desc()).all()


@router.get("/models/{model_id}", response_model=Model3DOut)
@safe_api
def get_model(model_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    model = db.query(Model3D).filter(Model3D.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="3D模型不存在")
    return model


@router.get("/models/{model_id}/parts", response_model=list[Model3DPartOut])
@safe_api
def list_parts(model_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return (
        db.query(Model3DPart)
        .filter(Model3DPart.model_3d_id == model_id)
        .all()
    )


@router.get("/models/{model_id}/animations", response_model=list[Model3DAnimationOut])
@safe_api
def list_animations(model_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return (
        db.query(Model3DAnimation)
        .filter(Model3DAnimation.model_3d_id == model_id)
        .all()
    )


@router.get("/forklift/{forklift_model_id}")
@safe_api
def get_forklift_3d(forklift_model_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """根据叉车车型ID获取3D模型"""
    model = (
        db.query(Model3D)
        .filter(Model3D.forklift_model_id == forklift_model_id)
        .first()
    )
    if not model:
        raise HTTPException(status_code=404, detail="该车型暂无3D模型")

    parts = (
        db.query(Model3DPart)
        .filter(Model3DPart.model_3d_id == model.id)
        .all()
    )
    animations = (
        db.query(Model3DAnimation)
        .filter(Model3DAnimation.model_3d_id == model.id)
        .all()
    )

    return {
        "model": Model3DOut.model_validate(model),
        "parts": [Model3DPartOut.model_validate(p) for p in parts],
        "animations": [Model3DAnimationOut.model_validate(a) for a in animations],
    }


# ========== AR ==========

ar_router = APIRouter(prefix="/ar", tags=["AR实景"])


@ar_router.get("/config/{forklift_model_id}", response_model=ArConfigOut)
@safe_api
def get_ar_config(forklift_model_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """获取叉车的AR配置（真实尺寸）"""
    config = (
        db.query(ArModelConfig)
        .filter(ArModelConfig.forklift_model_id == forklift_model_id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="该车型暂无AR配置")
    return config


@ar_router.get("/models")
@safe_api
def list_ar_models(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """列出所有有AR配置的车型"""
    configs = db.query(ArModelConfig).all()
    result = []
    for c in configs:
        model_3d = db.query(Model3D).filter(Model3D.id == c.model_3d_id).first()
        if model_3d:
            result.append({
                "config": ArConfigOut.model_validate(c),
                "model_3d": Model3DOut.model_validate(model_3d),
            })
    return result
