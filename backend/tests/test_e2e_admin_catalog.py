"""后台管理端 E2E：目录 CRUD、故障码/故障树、图纸资产与审计日志

覆盖重点：
- 目录数据的建/改/删与级联删除保护（品牌→系列→车型）
- 版权合规校验（MASTER_PLAN 4.3）在管理端创建资产时的拦截
- admin_audit_logs 落库：account-service 的管理员在本地 users 表没有投影，
  AdminPrincipal.id 解析为 None 时 admin_user_id 必须能写 NULL，
  否则所有后台写接口都会 500（历史 bug，用测试固化）
"""
import uuid

from conftest import mint_admin_token, mint_user_token


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def admin_headers() -> dict:
    # 13800000000 在本地 users 表没有记录 → 走 admin_user_id IS NULL 的路径
    return auth(mint_admin_token("13800000000", "super_admin"))


def tag() -> str:
    return uuid.uuid4().hex[:8]


# ========== 车型目录 ==========


def test_admin_catalog_brand_series_model_lifecycle(client):
    h = admin_headers()
    t = tag()

    brand = client.post("/api/v1/admin/catalog/brands", headers=h, json={"name": f"E2E品牌-{t}"})
    assert brand.status_code == 200, brand.text
    brand_id = brand.json()["id"]
    assert brand.json()["series_count"] == 0

    # 重名拦截
    dup = client.post("/api/v1/admin/catalog/brands", headers=h, json={"name": f"E2E品牌-{t}"})
    assert dup.status_code == 400

    # 改品牌
    updated = client.put(f"/api/v1/admin/catalog/brands/{brand_id}", headers=h, json={"country": "DE"})
    assert updated.status_code == 200
    assert updated.json()["country"] == "DE"

    # 系列 → 车型
    series = client.post(
        "/api/v1/admin/catalog/series", headers=h,
        json={"brand_id": brand_id, "name": f"E2E系列-{t}"},
    )
    assert series.status_code == 200, series.text
    series_id = series.json()["id"]
    assert series.json()["brand_name"] == f"E2E品牌-{t}"

    model = client.post(
        "/api/v1/admin/catalog/models", headers=h,
        json={"series_id": series_id, "name": f"E2E车型-{t}", "load_capacity_kg": 1500, "fuel_type": "electric"},
    )
    assert model.status_code == 200, model.text
    model_id = model.json()["id"]

    renamed = client.put(
        f"/api/v1/admin/catalog/models/{model_id}", headers=h,
        json={"load_capacity_kg": 2000},
    )
    assert renamed.status_code == 200
    assert renamed.json()["load_capacity_kg"] == 2000

    # 关键字搜索能命中
    listing = client.get("/api/v1/admin/catalog/models", headers=h, params={"keyword": f"E2E车型-{t}"})
    assert listing.status_code == 200
    ids = [m["id"] for m in listing.json()["items"]]
    assert ids == [model_id], listing.json()

    # 级联删除保护：有车型时不能删系列，有系列时不能删品牌
    assert client.delete(f"/api/v1/admin/catalog/series/{series_id}", headers=h).status_code == 400
    assert client.delete(f"/api/v1/admin/catalog/brands/{brand_id}", headers=h).status_code == 400

    # 逐层删除成功
    assert client.delete(f"/api/v1/admin/catalog/models/{model_id}", headers=h).status_code == 200
    assert client.delete(f"/api/v1/admin/catalog/series/{series_id}", headers=h).status_code == 200
    assert client.delete(f"/api/v1/admin/catalog/brands/{brand_id}", headers=h).status_code == 200

    # 不存在的 id 一律 404
    assert client.put(f"/api/v1/admin/catalog/brands/999999", headers=h, json={"name": "x"}).status_code == 404
    assert client.delete(f"/api/v1/admin/catalog/models/{model_id}", headers=h).status_code == 404


def test_admin_engine_and_parts_crud(client):
    h = admin_headers()
    t = tag()

    eb = client.post("/api/v1/admin/catalog/engine-brands", headers=h, json={"name": f"E2E发动机-{t}"})
    assert eb.status_code == 200, eb.text
    eb_id = eb.json()["id"]

    em = client.post(
        "/api/v1/admin/catalog/engine-models", headers=h,
        json={"brand_id": eb_id, "model_name": f"EM-{t}", "displacement": "2.3", "power_kw": 88},
    )
    assert em.status_code == 200, em.text
    em_id = em.json()["id"]
    assert em.json()["brand_name"] == f"E2E发动机-{t}"

    em_updated = client.put(
        f"/api/v1/admin/catalog/engine-models/{em_id}", headers=h, json={"power_hp": 120}
    )
    assert em_updated.status_code == 200
    assert em_updated.json()["power_hp"] == 120

    part = client.post(
        "/api/v1/admin/catalog/parts", headers=h,
        json={"oem_number": f"OEM-{t}", "name": f"E2E滤芯-{t}", "category": "filter", "price_reference": 88.5},
    )
    assert part.status_code == 200, part.text
    part_id = part.json()["id"]

    part_updated = client.put(f"/api/v1/admin/catalog/parts/{part_id}", headers=h, json={"unit": "套"})
    assert part_updated.status_code == 200
    assert part_updated.json()["unit"] == "套"

    assert client.delete(f"/api/v1/admin/catalog/parts/{part_id}", headers=h).status_code == 200
    assert client.delete(f"/api/v1/admin/catalog/engine-models/{em_id}", headers=h).status_code == 200
    assert client.delete(f"/api/v1/admin/catalog/engine-brands/{eb_id}", headers=h).status_code == 200


def test_admin_catalog_keyword_escapes_wildcards(client):
    """关键字里的 % 是通配符，必须被转义，否则会放大匹配范围"""
    h = admin_headers()
    t = tag()
    client.post("/api/v1/admin/catalog/brands", headers=h, json={"name": f"百分号{t}"})

    # 只带通配符、不带品牌前缀时不应命中刚建的记录
    loose = client.get("/api/v1/admin/catalog/brands", headers=h, params={"keyword": "%"})
    assert loose.status_code == 200
    assert not any(f"百分号{t}" in b["name"] for b in loose.json()["items"])

    strict = client.get("/api/v1/admin/catalog/brands", headers=h, params={"keyword": f"百分号{t}"})
    assert any(f"百分号{t}" in b["name"] for b in strict.json()["items"])


# ========== 故障码 / 故障树 ==========


def test_admin_fault_code_and_tree_crud(client):
    h = admin_headers()
    t = tag()

    code = client.post(
        "/api/v1/admin/knowledge/fault-codes", headers=h,
        json={"code": f"E2E-F{t}", "description": "测试故障描述", "severity": "medium", "category": "hydraulic"},
    )
    assert code.status_code == 200, code.text
    code_id = code.json()["id"]

    tree = client.post(
        "/api/v1/admin/knowledge/fault-trees", headers=h,
        json={
            "fault_code_id": code_id,
            "symptom": f"举升缓慢-{t}",
            "causes_json": ["油泵磨损", "滤芯堵塞"],
            "solutions_json": ["更换滤芯"],
            "probability_json": {"油泵磨损": 0.6},
        },
    )
    assert tree.status_code == 200, tree.text
    tree_id = tree.json()["id"]

    tree_updated = client.put(
        f"/api/v1/admin/knowledge/fault-trees/{tree_id}", headers=h, json={"symptom": "举升无力"}
    )
    assert tree_updated.status_code == 200
    assert tree_updated.json()["symptom"] == "举升无力"

    assert client.delete(f"/api/v1/admin/knowledge/fault-trees/{tree_id}", headers=h).status_code == 200
    assert client.delete(f"/api/v1/admin/knowledge/fault-codes/{code_id}", headers=h).status_code == 200

    # 普通用户令牌不能碰后台
    assert client.get("/api/v1/admin/knowledge/fault-codes", headers=auth(mint_user_token("13900009999"))).status_code == 401


# ========== 图纸资产与版权合规 ==========


def test_admin_diagram_copyright_rules(client, catalog):
    h = admin_headers()

    # 缺必填字段
    assert client.post("/api/v1/admin/assets/diagrams", headers=h, json={}).status_code == 422

    # 非法图类型
    bad_shape = client.post(
        "/api/v1/admin/assets/diagrams", headers=h,
        json={"diagram_type": "hydraulic", "image_url": "http://x/a.png"},
    )
    assert bad_shape.status_code == 400

    # 非法授权类型
    bad_type = client.post(
        "/api/v1/admin/assets/diagrams", headers=h,
        json={"diagram_type": "structure", "image_url": "http://x/a.png", "license_type": "unknown_type"},
    )
    assert bad_type.status_code == 400

    # 标记可商用但未填版权所有者
    no_owner = client.post(
        "/api/v1/admin/assets/diagrams", headers=h,
        json={"diagram_type": "structure", "image_url": "http://x/a.png", "commercial_use": True},
    )
    assert no_owner.status_code == 400

    # 授权类型不允许商用
    wrong_license = client.post(
        "/api/v1/admin/assets/diagrams", headers=h,
        json={
            "diagram_type": "structure", "image_url": "http://x/a.png",
            "commercial_use": True, "copyright_owner": "供应商A", "license_type": "internal_only",
        },
    )
    assert wrong_license.status_code == 400

    # 合规创建
    ok = client.post(
        "/api/v1/admin/assets/diagrams", headers=h,
        json={
            "diagram_type": "structure", "image_url": "http://x/a.png", "title": "测试结构图",
            "model_id": catalog["model_id"],
            "copyright_owner": "供应商A", "license_type": "licensed", "commercial_use": True,
        },
    )
    assert ok.status_code == 200, ok.text
    diagram_id = ok.json()["id"]

    # 已存在时可回填历史到期时间
    retro = client.put(
        f"/api/v1/admin/assets/diagrams/{diagram_id}", headers=h,
        json={"license_expire": "2020-01-01T00:00:00"},
    )
    assert retro.status_code == 200

    # 新建时到期时间必须在未来
    future_only = client.post(
        "/api/v1/admin/assets/diagrams", headers=h,
        json={"diagram_type": "engine", "image_url": "http://x/b.png", "license_expire": "2020-01-01T00:00:00"},
    )
    assert future_only.status_code == 400

    assert client.delete(f"/api/v1/admin/assets/diagrams/{diagram_id}", headers=h).status_code == 200


def test_admin_knowledge_document_copyright_rules(client):
    """知识库文档的版权校验在创建和更新时都要生效"""
    h = admin_headers()
    t = tag()

    bad_type = client.post(
        "/api/v1/admin/knowledge/documents", headers=h,
        json={"title": f"非法授权-{t}", "license_type": "unknown_type"},
    )
    assert bad_type.status_code == 400

    no_owner = client.post(
        "/api/v1/admin/knowledge/documents", headers=h,
        json={"title": f"缺版权所有者-{t}", "commercial_use": True},
    )
    assert no_owner.status_code == 400

    ok = client.post(
        "/api/v1/admin/knowledge/documents", headers=h,
        json={
            "title": f"合规文档-{t}", "content": "正文", "doc_type": "manual",
            "license_type": "cc0", "copyright_owner": "测试", "commercial_use": True,
        },
    )
    assert ok.status_code == 200, ok.text
    doc_id = ok.json()["id"]

    # 更新时把可商用改成缺所有者也应被拒
    bad_update = client.put(
        f"/api/v1/admin/knowledge/documents/{doc_id}", headers=h,
        json={"license_type": "internal_only"},
    )
    assert bad_update.status_code == 400

    assert client.delete(f"/api/v1/admin/knowledge/documents/{doc_id}", headers=h).status_code == 200


def test_knowledge_router_also_enforces_copyright(client):
    """/api/v1/knowledge 与 /api/v1/admin/knowledge 是两个独立路由，两边都要校验"""
    h = admin_headers()
    t = tag()

    resp = client.post(
        "/api/v1/knowledge/documents", headers=h,
        json={"title": f"缺版权所有者-{t}", "commercial_use": True},
    )
    assert resp.status_code == 400, resp.text

    ok = client.post(
        "/api/v1/knowledge/documents", headers=h,
        json={"title": f"合规文档-{t}", "doc_type": "manual", "license_type": "cc_by"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["license_type"] == "cc_by"


# ========== 审计日志 ==========


def test_admin_audit_log_allows_external_admin(client, db_session):
    """account-service 管理员在本地没有 users 投影时，审计日志要能带 NULL 落库。

    admin_user_id 曾声明为 NOT NULL，导致 25+ 处后台写接口全部 500。
    """
    from app.models.admin_audit_logs import AdminAuditLogs

    def created_brand_audits():
        return (
            db_session.query(AdminAuditLogs)
            .filter(AdminAuditLogs.action == "create", AdminAuditLogs.target_type == "forklift_brand")
            .all()
        )

    h = admin_headers()
    t = tag()
    before = len(created_brand_audits())

    resp = client.post(
        "/api/v1/admin/catalog/brands", headers=h, json={"name": f"审计验证-{t}"}
    )
    assert resp.status_code == 200, resp.text
    brand_id = resp.json()["id"]

    rows = created_brand_audits()
    assert len(rows) == before + 1, f"应新增 1 条审计日志，实际新增 {len(rows) - before}"
    row = rows[-1]
    assert row.admin_user_id is None
    assert row.target_id == brand_id
    assert isinstance(row.after_json, dict) and row.after_json["id"] == brand_id
