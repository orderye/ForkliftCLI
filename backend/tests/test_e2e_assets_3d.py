"""3D 模型与 AR 资产的 E2E：上传版本化、C 端下发、授权过期隐藏、后台管理

覆盖 app/api/model3d.py 与 app/api/admin/assets.py 的模型分支，
以及 app/core/storage.py 的本地存储写入与路径校验。
"""
import uuid
from datetime import datetime, timedelta, timezone

from conftest import create_user, mint_admin_token, mint_user_token


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_headers() -> dict:
    return auth(mint_admin_token())


def uploader_headers(phone: str = "13900009901") -> dict:
    """C 端接口要求令牌里的手机号在本地 users 表有投影"""
    user = create_user(phone)
    return auth(mint_user_token(user.phone))


def glb_bytes(tag: str) -> bytes:
    """造一段内容唯一的假二进制（不校验 glTF 结构，存储层只按字节处理）"""
    return f"glTF-{tag}-{uuid.uuid4().hex}".encode()


def upload(client, headers: dict, tag: str, forklift_model_id=None, name=None):
    files = {"file": (f"{tag}.glb", glb_bytes(tag), "model/gltf-binary")}
    data = {"name": name or f"E2E模型-{tag}"}
    if forklift_model_id is not None:
        data["forklift_model_id"] = str(forklift_model_id)
    return client.post("/api/v1/3d/upload", headers=headers, data=data, files=files)


# ========== 上传与版本化 ==========


def test_3d_upload_creates_and_bumps_version(client, catalog):
    h = uploader_headers()

    first = upload(client, h, "v1", forklift_model_id=catalog["model_id"])
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["version"] == 1
    assert body["format"] == "glb"
    assert body["status"] == "ready"
    assert body["content_hash"] and len(body["content_hash"]) == 64
    assert body["storage_provider"] == "local"
    assert body["file_url"].startswith("/uploads/models/")

    second = upload(client, h, "v2", forklift_model_id=catalog["model_id"])
    assert second.status_code == 200, second.text
    assert second.json()["version"] == 2
    assert second.json()["content_hash"] != body["content_hash"]

    # 按车型取模型时返回最新版本
    latest = client.get(f"/api/v1/3d/forklift/{catalog['model_id']}", headers=h)
    assert latest.status_code == 200
    assert latest.json()["model"]["version"] == 2

    # 未授权访问被拒，不存在的车型 404
    assert client.get(f"/api/v1/3d/forklift/{catalog['model_id']}").status_code == 401
    assert client.get("/api/v1/3d/forklift/999999", headers=h).status_code == 404


def test_3d_upload_rejects_bad_format_and_empty_file(client):
    h = uploader_headers("13900009902")

    bad = client.post(
        "/api/v1/3d/upload", headers=h,
        data={"name": "非法格式", "format": "obj"},
        files={"file": ("x.obj", b"data", "application/octet-stream")},
    )
    assert bad.status_code == 400, bad.text

    empty = client.post(
        "/api/v1/3d/upload", headers=h,
        data={"name": "空文件"},
        files={"file": ("x.glb", b"", "model/gltf-binary")},
    )
    assert empty.status_code == 400, empty.text

    missing = client.post("/api/v1/3d/upload", headers=h)
    assert missing.status_code == 422


def test_3d_upload_validates_file_magic(client):
    """format 由客户端声明，服务端必须再用文件内容验一遍，否则改后缀就能绕过"""
    h = uploader_headers("13900009906")

    def up(filename: str, content: bytes, fmt: str | None = None):
        data = {"name": filename}
        if fmt:
            data["format"] = fmt
        return client.post(
            "/api/v1/3d/upload", headers=h,
            data=data, files={"file": (filename, content, "application/octet-stream")},
        )

    # 声称 glb，内容其实是文本
    fake = up("fake.glb", b"this is not a glb at all")
    assert fake.status_code == 400, fake.text
    assert "GLB" in fake.text

    # 连魔数长度都不够
    assert up("short.glb", b"glTF").status_code == 400

    # 声称 gltf，内容不是 JSON
    assert up("fake.gltf", b"not json", fmt="gltf").status_code == 400

    # JSON 但不是 glTF 描述（缺 asset 段）
    assert up("partial.gltf", b'{"materials": []}', fmt="gltf").status_code == 400

    # 合法的 glTF 描述通过
    ok = up("real.gltf", b'{"asset": {"version": "2.0"}}', fmt="gltf")
    assert ok.status_code == 200, ok.text
    assert ok.json()["format"] == "gltf"


# ========== 零件 / 动画 / AR 配置 ==========


def test_3d_parts_animations_and_ar_config(client, catalog, db_session):
    from app.models.model3d import ArModelConfig, Model3DAnimation, Model3DPart

    h = uploader_headers("13900009903")
    model_id = upload(client, h, "full", forklift_model_id=catalog["model_id"]).json()["id"]

    db_session.add(Model3DPart(model_3d_id=model_id, name="货叉", group="fork", material="steel"))
    db_session.add(Model3DPart(model_3d_id=model_id, name="门架", group="mast"))
    db_session.add(
        Model3DAnimation(model_3d_id=model_id, name="mast_up", display_name="门架上升", duration_ms=800)
    )
    db_session.flush()
    db_session.add(ArModelConfig(
        model_3d_id=model_id,
        forklift_model_id=catalog["model_id"],
        real_length_mm=2970, real_width_mm=1190, real_height_mm=2095,
        real_mast_height_mm=3200, real_wheelbase_mm=1135,
        real_turning_radius_mm=1930, scale_factor=0.5,
    ))
    db_session.commit()

    parts = client.get(f"/api/v1/3d/models/{model_id}/parts", headers=h)
    assert parts.status_code == 200
    assert {p["group"] for p in parts.json()} == {"fork", "mast"}

    animations = client.get(f"/api/v1/3d/models/{model_id}/animations", headers=h)
    assert animations.status_code == 200
    assert animations.json()[0]["name"] == "mast_up"

    config = client.get(f"/api/v1/ar/config/{catalog['model_id']}", headers=h)
    assert config.status_code == 200
    assert config.json()["real_length_mm"] == 2970
    assert config.json()["scale_factor"] == 0.5

    ar_models = client.get("/api/v1/ar/models", headers=h)
    assert ar_models.status_code == 200
    assert any(m["config"]["id"] == config.json()["id"] for m in ar_models.json())

    # 没有 AR 配置的车型 404
    assert client.get("/api/v1/ar/config/999999", headers=h).status_code == 404


# ========== 授权过期隐藏 ==========


def test_3d_license_expiry_hides_model_from_c_client(client, db_session):
    from app.models.model3d import Model3D

    h = uploader_headers("13900009904")
    model_id = upload(client, h, "licensed").json()["id"]

    listed = client.get("/api/v1/3d/models", headers=h)
    assert listed.status_code == 200
    assert model_id in [m["id"] for m in listed.json()]

    # license_expire 为 NULL 表示永久授权，填一个过去的时间模拟到期
    db_session.query(Model3D).filter(Model3D.id == model_id).update(
        {"license_expire": datetime.now(timezone.utc) - timedelta(days=1)}
    )
    db_session.commit()

    after = client.get("/api/v1/3d/models", headers=h)
    assert after.status_code == 200
    assert model_id not in [m["id"] for m in after.json()], "授权过期的 3D 模型不应下发"

    detail = client.get(f"/api/v1/3d/models/{model_id}", headers=h)
    assert detail.status_code == 404
    assert "授权" in detail.json()["message"]

    # 后台仍然可见（管理员视角）
    admin_list = client.get("/api/v1/admin/assets/models3d", headers=admin_headers())
    assert admin_list.status_code == 200
    assert model_id in [m["id"] for m in admin_list.json()["items"]]


# ========== 后台管理 ==========


def test_admin_models3d_update_and_delete_cascades(client, db_session):
    from app.models.model3d import Model3DPart

    h = uploader_headers("13900009905")
    model_id = upload(client, h, "admin").json()["id"]
    db_session.add(Model3DPart(model_3d_id=model_id, name="驱动轮", group="transmission"))
    db_session.commit()

    ah = admin_headers()

    # 非法状态、非法授权类型、不存在的关联车型都要被拒
    # （此前 update 分支调用了未导入的 validate_copyright，会直接 500）
    assert client.put(f"/api/v1/admin/assets/models3d/{model_id}", headers=ah,
                      json={"status": "half-done"}).status_code == 400
    assert client.put(f"/api/v1/admin/assets/models3d/{model_id}", headers=ah,
                      json={"license_type": "unknown_type"}).status_code == 400
    assert client.put(f"/api/v1/admin/assets/models3d/{model_id}", headers=ah,
                      json={"forklift_model_id": 999999}).status_code == 400

    updated = client.put(
        f"/api/v1/admin/assets/models3d/{model_id}", headers=ah,
        json={"name": "改名后的模型", "status": "error", "copyright_owner": "供应商B",
              "license_type": "licensed", "commercial_use": True},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "error"
    assert updated.json()["copyright_owner"] == "供应商B"

    # 状态过滤生效
    filtered = client.get("/api/v1/admin/assets/models3d", headers=ah, params={"status": "error"})
    assert filtered.status_code == 200
    assert filtered.json()["items"]
    assert all(m["status"] == "error" for m in filtered.json()["items"])

    assert client.delete(f"/api/v1/admin/assets/models3d/{model_id}", headers=ah).status_code == 200
    assert client.get(f"/api/v1/3d/models/{model_id}", headers=h).status_code == 404
    # 零件随 relationship cascade 一起删除
    assert client.get(f"/api/v1/3d/models/{model_id}/parts", headers=h).json() == []
    assert client.delete(f"/api/v1/admin/assets/models3d/{model_id}", headers=ah).status_code == 404
