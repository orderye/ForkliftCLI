import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.core.security import get_current_user
from app.core.storage import get_storage_client
from app.models.user import User
from app.models.model3d import Model3D, Model3DPart, Model3DAnimation, ArModelConfig
from app.models.copyright_mixin import license_active_condition
from app.schemas.model3d import Model3DOut, Model3DPartOut, Model3DAnimationOut, ArConfigOut
from app.schemas.model3d import Model3DCreate
from datetime import datetime, timezone

router = APIRouter(prefix="/3d", tags=["3D模型"])


def _validate_model_bytes(data: bytes, fmt: str) -> None:
    """用文件内容校验格式声明。format 由客户端提交，只靠白名单容易被改后缀绕过。"""
    if fmt == "glb":
        # GLB 容器固定以 ASCII 魔数 "glTF" 开头
        if len(data) < 12 or data[:4] != b"glTF":
            raise HTTPException(400, "文件内容不是 GLB 格式")
        return
    if fmt == "gltf":
        try:
            payload = json.loads(data.decode("utf-8-sig"))
        except Exception:
            raise HTTPException(400, "文件内容不是 glTF JSON 格式")
        if not isinstance(payload, dict) or "asset" not in payload:
            raise HTTPException(400, "文件内容不是合法的 glTF 描述（缺少 asset 段）")
        return
    raise HTTPException(400, f"不支持格式 {fmt}，仅接受 glb / gltf")


def _mime_of_format(fmt: str) -> str:
    """返回 .glb / .gltf 对应的 Content-Type。"""
    f = (fmt or "glb").lower()
    if f == "gltf":
        return "model/gltf+json"
    return "model/gltf-binary"


@router.get("/models", response_model=list[Model3DOut])
@safe_api
def list_models(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return (
        db.query(Model3D)
        .filter(license_active_condition(Model3D.license_expire))  # 授权过期的模型不下发
        .order_by(Model3D.created_at.desc())
        .all()
    )


@router.get("/models/{model_id}", response_model=Model3DOut)
@safe_api
def get_model(model_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    model = db.query(Model3D).filter(Model3D.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="3D模型不存在")
    if model.license_expired:
        raise HTTPException(status_code=404, detail="该3D模型授权已到期")
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
    """根据叉车车型ID获取3D模型（返回最新版本）"""
    model = (
        db.query(Model3D)
        .filter(
            Model3D.forklift_model_id == forklift_model_id,
            license_active_condition(Model3D.license_expire),  # 与列表接口一致，授权过期的不下发
        )
        .order_by(Model3D.version.desc())
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


@router.post("/upload", response_model=Model3DOut)
@safe_api
async def upload_3d_model(
    file: UploadFile = File(...),
    forklift_model_id: int | None = Form(None),
    name: str = Form(...),
    description: str = Form(""),
    format: str = Form("glb"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    上传 3D 模型到对象存储，返回模型元数据（含 version、content_hash）。
    - 若已有相同 forklift_model_id 的模型，自动递增版本；
    - 若内容哈希完全一致，可跳过存储（按需）；
    """
    allowed_formats = ("glb", "gltf")
    if format.lower() not in allowed_formats:
        raise HTTPException(400, f"不支持格式 {format}，仅接受 glb / gltf")

    data = await file.read()
    if not data:
        raise HTTPException(400, "文件为空")

    _validate_model_bytes(data, format.lower())

    storage = get_storage_client()
    content_hash = storage.compute_hash(data)
    mime = _mime_of_format(format)

    # 生成 storage key：models/{forklift_model_id}/{hash}.{ext}
    key_base = f"models/{forklift_model_id or 'general'}"
    file_key = f"{key_base}/{content_hash[:16]}.{format.lower()}"

    # 存储到对象存储（本地目录或 MinIO/S3）
    file_url = storage.put_object(file_key, data, content_type=mime)

    # 确定版本号
    existing = (
        db.query(Model3D)
        .filter(Model3D.forklift_model_id == forklift_model_id)
        .order_by(Model3D.version.desc())
        .first()
    )
    version = 1
    if existing:
        # 若内容哈希相同则视为同一版本；否则递增
        if existing.content_hash == content_hash:
            # 无实质变化，更新 updated_at 后返回现有记录
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return Model3DOut.model_validate(existing)
        version = (existing.version or 0) + 1

    file_size_mb = round(len(data) / (1024 * 1024), 3)

    model = Model3D(
        forklift_model_id=forklift_model_id,
        name=name,
        description=description,
        file_url=file_url,
        file_size_mb=file_size_mb,
        format=format.lower(),
        version=version,
        content_hash=content_hash,
        storage_provider=storage.provider,
        storage_key=file_key,
        mime_type=mime,
        uploaded_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        license_type="user_uploaded",  # 用户上传，责任归上传者；管理员可在后台修正
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    return Model3DOut.model_validate(model)


@router.post("/{model_id}/release", response_model=Model3DOut)
@safe_api
async def release_3d_model(
    model_id: int,
    file: UploadFile = File(...),
    format: str = Form("glb"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    为已有模型发布新版本（强制递增版本号）。
    """
    model = db.query(Model3D).filter(Model3D.id == model_id).first()
    if not model:
        raise HTTPException(404, "模型不存在")

    data = await file.read()
    if not data:
        raise HTTPException(400, "文件为空")

    _validate_model_bytes(data, format.lower())

    storage = get_storage_client()
    content_hash = storage.compute_hash(data)
    mime = _mime_of_format(format)
    new_version = (model.version or 0) + 1
    key_base = f"models/{model.forklift_model_id or 'general'}"
    file_key = f"{key_base}/{content_hash[:16]}.{format.lower()}"
    file_url = storage.put_object(file_key, data, content_type=mime)

    model.file_url = file_url
    model.file_size_mb = round(len(data) / (1024 * 1024), 3)
    model.format = format.lower()
    model.version = new_version
    model.content_hash = content_hash
    model.storage_provider = storage.provider
    model.storage_key = file_key
    model.mime_type = mime
    model.uploaded_at = datetime.now(timezone.utc)
    model.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(model)

    return Model3DOut.model_validate(model)
