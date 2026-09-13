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


# ========== P1-6: list_ar_models N+1 与授权过滤 ==========
#
# 修复前：list_ar_models 对每个 ArModelConfig 单独查 Model3d，N+1。
# 修复后：单次 IN 查询；同时过滤掉 license_expire <= now 的模型。
# 这条用例同时验证：返回数量正确、不返回过期模型、未注册 AR 的车型不影响。
# 直接 query count 不靠谱（SQLAlchemy session 有缓存），改用事件探针：
# 监听 engine 的 before_cursor_execute 事件统计 SELECT 数量，确保即使有 N 个
# ArModelConfig 也只产生少量 Model3D 查询。


def _attach_select_counter(db_session):
    """挂一个 SELECT 语句计数器到 engine，返回计数器与卸载函数。"""
    from sqlalchemy import event

    counter = {"selects": 0, "tables": []}

    def _record(conn, cursor, statement, params, context, executemany):
        if not statement.lstrip().upper().startswith("SELECT"):
            return
        counter["selects"] += 1
        # 抓表名（粗略，按 FROM 之后到 WHERE 之前的 token）
        upper = statement.upper()
        if "FROM MODEL_3D" in upper or "FROM MODEL_3D " in upper:
            counter["tables"].append("model_3d")

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", _record)

    def _uninstall():
        event.remove(engine, "before_cursor_execute", _record)

    return counter, _uninstall


def test_list_ar_models_uses_single_query_and_filters_expired(client, db_session, catalog):
    """P1-6 修复回归。

    1) 多条 ArModelConfig 必须只产生 1 条 SELECT model_3d 查询（去 N+1）；
    2) license_expire <= now 的模型不应出现在列表中；
    3) list_ar_models 整体在无任何 AR 配置时返回空列表（边界）。
    """
    from app.models.model3d import ArModelConfig, Model3D

    h = uploader_headers("13900009910")
    # 上传 3 个模型：2 个有 AR 配置（1 个授权永久、1 个授权过期），1 个无 AR 配置。
    m_forever = upload(client, h, "ar-forever", forklift_model_id=catalog["model_id"]).json()["id"]
    m_expired = upload(client, h, "ar-expired").json()["id"]
    m_no_ar = upload(client, h, "no-ar").json()["id"]

    db_session.add(ArModelConfig(model_3d_id=m_forever, forklift_model_id=catalog["model_id"]))
    db_session.add(ArModelConfig(model_3d_id=m_expired, forklift_model_id=catalog["model_id"]))
    # 把 m_expired 的 license_expire 设为过去
    db_session.query(Model3D).filter(Model3D.id == m_expired).update(
        {"license_expire": datetime.now(timezone.utc) - timedelta(days=1)}
    )
    db_session.commit()

    counter, uninstall = _attach_select_counter(db_session)
    try:
        resp = client.get("/api/v1/ar/models", headers=h)
    finally:
        uninstall()

    assert resp.status_code == 200, resp.text
    items = resp.json()
    # 修复后：1 条 ArModelConfig（m_forever）+ 1 条（m_expired 但被过滤）→ 实际
    # 列表里只有 m_forever。m_no_ar 没注册 AR 配置，不在考虑范围。
    returned_model_ids = [it["model_3d"]["id"] for it in items]
    assert m_forever in returned_model_ids
    assert m_expired not in returned_model_ids, "授权过期的模型不应进入 AR 列表"
    assert m_no_ar not in returned_model_ids

    # 核心断言：单次 SELECT model_3d 拉走所有关联的 model。
    # 注意：list_ar_models 还有「configs 列表」+「model_by_id」两次查询，
    # 但对 model_3d 表的 SELECT 应当 ≤ 1。
    model_3d_selects = counter["tables"].count("model_3d")
    assert model_3d_selects <= 1, (
        f"list_ar_models 触发 {model_3d_selects} 次 model_3d SELECT，"
        f"出现 N+1 回归。完整 SELECT 序列：{counter}"
    )


def test_list_ar_models_empty_when_no_configs(client, db_session):
    """边界：没有任何 ArModelConfig 时返回空数组而非 500。"""
    h = uploader_headers("13900009911")
    # 确保干净：删掉测试期间已建的 ArModelConfig（其它测试可能残留）。
    from app.models.model3d import ArModelConfig
    db_session.query(ArModelConfig).delete()
    db_session.commit()

    resp = client.get("/api/v1/ar/models", headers=h)
    assert resp.status_code == 200
    assert resp.json() == []


# ========== P0-1: DRACOLoader 已删除 —— GLB 上传回归 ==========
#
# 修复前 viewer_full.html 引用未导入的 DRACOLoader，加载压缩 GLB 会 ReferenceError。
# 修复后删除 DRACOLoader 相关代码；后端 _validate_model_bytes 已用 magic 校验。
# 验证：DRACOLoader 路径不会污染上传链路，合法 GLB 仍能上传、合法 JSON glTF
# 也能上传，magic 校验（GLB 与 glTF JSON）正常工作。


def test_glb_upload_works_after_draco_removal(client, db_session, catalog):
    """P0-1 回归：DRACOLoader 路径删除后，后端 GLB 上传链路仍然完整。

    前端不再尝试启用 Draco 解码，模型必须在未启用 Draco 压缩的前提下可加载。
    这里直接验证最简合法 GLB（仅有 glTF magic）能被后端接受。
    """
    h = uploader_headers("13900009912")
    # 最小合法 GLB：12 字节头（magic + version + declared_length），无需 JSON chunk。
    # 后端只校验前 4 字节 magic 与文件长度 ≥ 12。
    minimal_glb = b"glTF" + (2).to_bytes(4, "little") + (12).to_bytes(4, "little")
    files = {"file": ("min.glb", minimal_glb, "model/gltf-binary")}
    data = {
        "name": "DRACO 修复回归",
        "format": "glb",
        "forklift_model_id": str(catalog["model_id"]),
    }
    resp = client.post("/api/v1/3d/upload", headers=h, files=files, data=data)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["format"] == "glb"
    assert body["content_hash"]
    assert body["file_url"].startswith("/uploads/models/")

    # 反向：声称 glb 但内容是文本（缺 magic）必须被 400 拒，与 magic 校验一致。
    bad = client.post(
        "/api/v1/3d/upload", headers=h,
        data={"name": "假 GLB", "format": "glb",
              "forklift_model_id": str(catalog["model_id"])},
        files={"file": ("x.glb", b"not a glb", "model/gltf-binary")},
    )
    assert bad.status_code == 400
    assert "GLB" in bad.text
