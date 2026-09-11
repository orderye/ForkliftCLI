"""端到端 API 测试：走真实迁移出的库 + FastAPI TestClient

不 mock 数据库、不 mock 依赖注入，只造真实数据，验证
「拍照识别 → 车型资料 → 维修档案 → 订阅门禁」这条主线端到端可用。
"""
import uuid

import pytest

from conftest import create_user, mint_admin_token, mint_user_token


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ========== 基础 ==========


def test_health_and_root(client):
    """status 恒为 ok（探活语义），依赖状态单独在 dependencies 里"""
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert set(body["dependencies"]) == {"redis"}
    assert body["dependencies"]["redis"] in {"up", "down", "not_configured"}

    root = client.get("/").json()
    assert root["name"] == "ForkliftCLI"
    assert root["docs"] == "/docs"


def test_unauthenticated_returns_401(client):
    for path in ("/api/v1/auth/profile", "/api/v1/my-forklifts", "/api/v1/3d/models"):
        assert client.get(path).status_code == 401, path


def test_invalid_and_unknown_token_rejected(client):
    assert client.get("/api/v1/auth/profile", headers=auth("not-a-jwt")).status_code == 401
    assert client.get("/api/v1/auth/profile", headers=auth(mint_user_token("99999999999"))).status_code == 401


# ========== 认证 ==========


def test_profile_get_and_update(client):
    user = create_user("13900000001")
    headers = auth(mint_user_token(user.phone))

    profile = client.get("/api/v1/auth/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["phone"] == user.phone
    assert profile.json()["subscription_level"] == "free"

    updated = client.put(
        "/api/v1/auth/profile",
        headers=headers,
        json={"nickname": "李师傅", "email": "li@example.com"},
    )
    assert updated.status_code == 200
    assert updated.json()["nickname"] == "李师傅"
    assert updated.json()["email"] == "li@example.com"


# ========== 车型库（含车型详情聚合链路） ==========


def test_forklift_catalog_chain(client, catalog):
    brands = client.get("/api/v1/forklifts/brands")
    assert brands.status_code == 200
    assert any(b["id"] == catalog["brand_id"] for b in brands.json())

    series = client.get(f"/api/v1/forklifts/brands/{catalog['brand_id']}/series")
    assert series.status_code == 200
    assert len(series.json()) == 1

    models = client.get(f"/api/v1/forklifts/series/{catalog['series_id']}/models")
    assert models.status_code == 200
    model = models.json()[0]
    assert model["name"] == "TEST-3T"

    detail = client.get(f"/api/v1/forklifts/models/{catalog['model_id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == catalog["model_id"]
    assert body["load_capacity_kg"] == 3000

    spec = client.get(f"/api/v1/forklifts/models/{catalog['model_id']}/specification")
    assert spec.status_code in (200, 404)
    assert spec.json().get("model_id") == catalog["model_id"] or spec.status_code == 404

    systems = client.get(f"/api/v1/forklifts/models/{catalog['model_id']}/systems")
    assert systems.status_code == 200
    assert systems.json() == []


def test_forklift_search(client, catalog):
    res = client.get("/api/v1/forklifts/search", params={"q": "TEST-3T"})
    assert res.status_code == 200
    assert any(m["id"] == catalog["model_id"] for m in res.json())

    assert client.get("/api/v1/forklifts/search").status_code == 422
    assert client.get("/api/v1/forklifts/search", params={"q": "不存在的型号"}).json() == []


def test_missing_model_returns_404(client):
    assert client.get("/api/v1/forklifts/models/99999").status_code == 404


# ========== 发动机库 ==========


def test_engine_catalog(client, catalog):
    brands = client.get("/api/v1/engines/brands")
    assert brands.status_code == 200
    assert any(b["id"] == catalog["engine_brand_id"] for b in brands.json())

    models = client.get(f"/api/v1/engines/brands/{catalog['engine_brand_id']}/models")
    assert models.status_code == 200
    assert models.json()[0]["model_name"] == "TE-100"

    detail = client.get(f"/api/v1/engines/models/{catalog['engine_model_id']}")
    assert detail.status_code == 200

    assert client.get("/api/v1/engines/models/99999").status_code == 404


# ========== 配件 ==========


def test_parts_search_and_detail(client, catalog):
    res = client.get("/api/v1/parts/search", params={"q": "TP-0001"})
    assert res.status_code == 200
    parts = res.json()["parts"]
    assert any(p["id"] == catalog["part_id"] for p in parts)

    detail = client.get(f"/api/v1/parts/{catalog['part_id']}")
    assert detail.status_code == 200

    assert client.get("/api/v1/parts/99999").status_code == 404


# ========== 维修档案（增删改查 + 保养提醒） ==========


@pytest.fixture()
def owner(client):
    user = create_user(f"1390000{uuid.uuid4().int % 10**7:07d}")
    return user, auth(mint_user_token(user.phone))


def test_my_forklifts_crud(client, catalog, owner):
    user, headers = owner

    assert client.get("/api/v1/my-forklifts", headers=headers).json() == []

    created = client.post(
        "/api/v1/my-forklifts",
        headers=headers,
        json={"forklift_model_id": catalog["model_id"], "serial_number": "SN-001", "customer_name": "张老板"},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["serial_number"] == "SN-001"
    assert body["model_name"] == "TEST-3T"

    forklift_id = body["id"]

    listed = client.get("/api/v1/my-forklifts", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    fetched = client.get(f"/api/v1/my-forklifts/{forklift_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["serial_number"] == "SN-001"

    updated = client.put(
        f"/api/v1/my-forklifts/{forklift_id}",
        headers=headers,
        json={"forklift_model_id": catalog["model_id"], "serial_number": "SN-002"},
    )
    assert updated.status_code == 200
    assert updated.json()["serial_number"] == "SN-002"

    deleted = client.delete(f"/api/v1/my-forklifts/{forklift_id}", headers=headers)
    assert deleted.status_code == 200
    assert client.get("/api/v1/my-forklifts", headers=headers).json() == []
    assert client.get(f"/api/v1/my-forklifts/{forklift_id}", headers=headers).status_code == 404


def test_other_users_forklift_is_inaccessible(client, catalog):
    a = create_user("13900000003")
    b = create_user("13900000004")

    created = client.post(
        "/api/v1/my-forklifts",
        headers=auth(mint_user_token(a.phone)),
        json={"forklift_model_id": catalog["model_id"]},
    )
    forklift_id = created.json()["id"]

    headers_b = auth(mint_user_token(b.phone))
    assert client.get(f"/api/v1/my-forklifts/{forklift_id}", headers=headers_b).status_code == 404
    assert client.delete(f"/api/v1/my-forklifts/{forklift_id}", headers=headers_b).status_code == 404


def test_maintenance_records_and_reminders(client, catalog, owner):
    _, headers = owner
    forklift_id = client.post(
        "/api/v1/my-forklifts", headers=headers,
        json={"forklift_model_id": catalog["model_id"], "serial_number": "SN-REM"},
    ).json()["id"]

    # 维修记录
    record = client.post(
        f"/api/v1/my-forklifts/{forklift_id}/records",
        headers=headers,
        json={"date": "2026-09-10", "fault_description": "举升缓慢", "technician": "李师傅", "cost": 350},
    )
    assert record.status_code == 200, record.text
    assert record.json()["fault_description"] == "举升缓慢"

    records = client.get(f"/api/v1/my-forklifts/{forklift_id}/records", headers=headers)
    assert records.status_code == 200
    assert len(records.json()) == 1

    # 保养提醒
    reminder = client.post(
        f"/api/v1/my-forklifts/{forklift_id}/reminders",
        headers=headers,
        json={"item_type": "hydraulic_oil", "item_name": "液压油", "interval_type": "hours", "interval_value": 200},
    )
    assert reminder.status_code == 200, reminder.text
    reminder_id = reminder.json()["id"]

    reminders = client.get(f"/api/v1/my-forklifts/{forklift_id}/reminders", headers=headers)
    assert reminders.status_code == 200
    assert len(reminders.json()) == 1

    toggled = client.patch(f"/api/v1/my-forklifts/reminders/{reminder_id}/toggle", headers=headers)
    assert toggled.status_code == 200
    assert toggled.json()["is_active"] == 0

    deleted = client.delete(f"/api/v1/my-forklifts/reminders/{reminder_id}", headers=headers)
    assert deleted.status_code == 200
    # 提醒接口没有单条查询，删除后用列表确认已移除
    remaining = client.get(f"/api/v1/my-forklifts/{forklift_id}/reminders", headers=headers)
    assert remaining.status_code == 200
    assert [r["id"] for r in remaining.json()] == []


# ========== 订阅与商业化 ==========


def test_subscription_is_forwarded_to_account_service(client, fake_account_service):
    """订阅状态由 account-service 权威提供，本服务只负责转发并透传令牌"""
    user = create_user("13900000005")
    headers = auth(mint_user_token(user.phone))

    res = client.get("/api/v1/subscription/me", headers=headers)
    assert res.status_code == 200, res.text
    assert res.json()["level"] == "pro"
    assert res.json()["trial_cards_remaining"] == 2

    # 令牌透传到 account-service，而不是用本地密钥重签
    assert fake_account_service.last_authorization == headers["Authorization"]
    assert fake_account_service.last_path == "/api/v1/subscription/me"


def test_subscription_activate_validates_plan(client, fake_account_service):
    user = create_user("13900000006")
    headers = auth(mint_user_token(user.phone))

    ok = client.post(
        "/api/v1/subscription/activate", headers=headers,
        json={"plan": "pro", "payment_id": "pay-1"},
    )
    assert ok.status_code == 200
    assert ok.json()["level"] == "pro"

    bad = client.post(
        "/api/v1/subscription/activate", headers=headers, json={"plan": "vip"},
    )
    assert bad.status_code == 400

    cancelled = client.post("/api/v1/subscription/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["cancelled"] is True


def test_enterprise_bind_limit(client, fake_account_service):
    """企业版最多绑定 5 个子账户（account-service 权威判定，本服务透传 403）"""
    user = create_user("13900000008", level="enterprise", expires_in_days=365)
    headers = auth(mint_user_token(user.phone))

    for i in range(5):
        res = client.post(
            "/api/v1/enterprise/bind_account",
            headers=headers,
            json={"phone_number": f"1390000100{i}"},
        )
        assert res.status_code == 200, res.text
        assert res.json()["bound"] is True

    sixth = client.post(
        "/api/v1/enterprise/bind_account",
        headers=headers,
        json={"phone_number": "13900001006"},
    )
    assert sixth.status_code == 403, f"第 6 个绑定应被拒绝，实际 {sixth.status_code}: {sixth.text}"


def test_enterprise_accounts_listing(client, fake_account_service):
    user = create_user("139000000085")
    headers = auth(mint_user_token(user.phone))
    res = client.get("/api/v1/enterprise/accounts", headers=headers)
    assert res.status_code == 200
    assert res.json()["accounts"] == []


# ========== 知识库（管理员权限） ==========


def test_knowledge_requires_admin(client):
    user = create_user("13900000009")
    assert client.get("/api/v1/knowledge/documents", headers=auth(mint_user_token(user.phone))).status_code in (401, 403)
    assert client.get("/api/v1/knowledge/documents").status_code == 401


def test_knowledge_crud_as_admin(client):
    headers = auth(mint_admin_token())

    listed = client.get("/api/v1/knowledge/documents", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 5  # 迁移播种的 5 篇文档

    created = client.post(
        "/api/v1/knowledge/documents",
        headers=headers,
        json={
            "title": "E2E 测试手册",
            "content": "这是端到端测试创建的维修手册内容。",
            "doc_type": "manual",
            "license_type": "self_owned",
            "copyright_owner": "测试",
        },
    )
    assert created.status_code == 200, created.text
    doc_id = created.json()["id"]
    assert created.json()["doc_type"] == "manual"

    assert client.get(f"/api/v1/knowledge/documents/{doc_id}", headers=headers).status_code == 200

    updated = client.put(
        f"/api/v1/knowledge/documents/{doc_id}",
        headers=headers,
        json={"title": "E2E 测试手册（改）", "license_type": "self_owned"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "E2E 测试手册（改）"

    assert client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/knowledge/documents/{doc_id}", headers=headers).status_code == 404


def test_knowledge_rejects_illegal_doc_type(client):
    headers = auth(mint_admin_token())
    res = client.post(
        "/api/v1/knowledge/documents",
        headers=headers,
        json={"title": "非法类型", "doc_type": "unknown"},
    )
    assert res.status_code == 400


def test_license_expiry_hides_asset_from_c_client(client, catalog, db_session):
    """授权过期的资产不应出现在 C 端（版权合规 4.3）

    创建时版权校验要求到期时间必须晚于当前时间，所以先合规创建，
    再把到期时间改到过去来模拟「时间流逝导致授权到期」。
    """
    from datetime import datetime, timedelta, timezone

    from app.models.ai import KnowledgeDocument

    admin = auth(mint_admin_token())
    user = create_user("13900000010")
    user_headers = auth(mint_user_token(user.phone))

    doc = client.post(
        "/api/v1/knowledge/documents",
        headers=admin,
        json={
            "title": "即将过期授权手册",
            "content": "内容",
            "doc_type": "manual",
            "forklift_model_id": catalog["model_id"],
            "license_type": "licensed",
            "copyright_owner": "供应商",
            "license_expire": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        },
    )
    assert doc.status_code == 200, doc.text
    doc_id = doc.json()["id"]

    def c_end_ids():
        res = client.get(f"/api/v1/manuals/model/{catalog['model_id']}", headers=user_headers)
        assert res.status_code == 200
        return [item["id"] for item in res.json()["items"]]

    # 未过期：C 端可见
    assert doc_id in c_end_ids(), "授权有效的手册应下发给 C 端"

    # 模拟到期
    db_session.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).update(
        {"license_expire": datetime.now(timezone.utc) - timedelta(days=1)}
    )
    db_session.commit()

    assert doc_id not in c_end_ids(), "授权已过期的手册不应下发给 C 端"

    # 后台仍能看见（管理员视角）
    assert client.get(f"/api/v1/knowledge/documents/{doc_id}", headers=admin).status_code == 200


# ========== 维修手册 ==========


def test_manuals_list_and_chunks(client, catalog, owner):
    admin = auth(mint_admin_token())
    _, headers = owner

    created = client.post(
        "/api/v1/knowledge/documents",
        headers=admin,
        json={
            "title": "C端可见手册",
            "content": "第一段内容。第二段内容。",
            "doc_type": "manual",
            "forklift_model_id": catalog["model_id"],
            "license_type": "self_owned",
        },
    )
    doc_id = created.json()["id"]

    listed = client.get("/api/v1/manuals", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == doc_id for item in listed.json()["items"])

    detail = client.get(f"/api/v1/manuals/{doc_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["title"] == "C端可见手册"

    chunks = client.get(f"/api/v1/manuals/{doc_id}/chunks", headers=headers)
    assert chunks.status_code == 200
    assert chunks.json() == []

    assert client.get("/api/v1/manuals/99999", headers=headers).status_code == 404


# ========== 3D / AR ==========


def test_3d_and_ar_endpoints(client, catalog, owner):
    _, headers = owner
    assert client.get("/api/v1/3d/models", headers=headers).status_code == 200
    assert client.get("/api/v1/ar/models", headers=headers).status_code == 200
    res = client.get(f"/api/v1/3d/forklift/{catalog['model_id']}", headers=headers)
    assert res.status_code in (200, 404)


# ========== 后台合规看板 ==========


def test_admin_compliance_and_dashboard(client, owner, catalog, fake_account_service):
    admin = auth(mint_admin_token())
    _, user_headers = owner

    summary = client.get("/api/v1/admin/compliance/summary", headers=admin)
    assert summary.status_code == 200
    assert "license_types" in summary.json() or isinstance(summary.json(), dict)

    stats = client.get("/api/v1/admin/dashboard/stats", headers=admin)
    assert stats.status_code == 200, stats.text
    # 看板把本地统计与 account-service 的账户维度统计聚合在一起
    body = stats.json()
    assert set(body) >= {"users", "enterprises", "payments", "trials", "subscriptions", "catalog", "assets", "ai", "maintenance"}
    assert body["catalog"]["brands"] >= 1

    expiring = client.get("/api/v1/admin/compliance/expiring", headers=admin, params={"days": 30})
    assert expiring.status_code == 200

    exported = client.get("/api/v1/admin/compliance/export", headers=admin)
    assert exported.status_code == 200

    # 普通用户令牌不能访问后台
    assert client.get("/api/v1/admin/dashboard/stats", headers=user_headers).status_code == 401


def test_admin_role_gate(client, fake_account_service):
    """operator 属于管理员（可访问），普通用户令牌必须被拒"""
    operator = auth(mint_admin_token(role="operator"))
    res = client.get("/api/v1/admin/users", headers=operator)
    assert res.status_code == 200
    assert res.json()["total"] == 0

    # 用户令牌（另一套密钥）不能访问后台
    user = create_user("13900000012")
    assert client.get("/api/v1/admin/users", headers=auth(mint_user_token(user.phone))).status_code == 401
    assert client.get("/api/v1/admin/users").status_code == 401


def test_admin_token_keys_are_isolated(client, fake_account_service):
    """管理员令牌用派生密钥，用户令牌打到后台接口必须 401"""
    user_token = auth(mint_user_token("13900000013"))
    assert client.get("/api/v1/admin/compliance/summary", headers=user_token).status_code == 401

    # 管理员令牌也不能通过用户接口验签
    admin_token = auth(mint_admin_token())
    assert client.get("/api/v1/auth/profile", headers=admin_token).status_code == 401


# ========== 支付 ==========


def test_payment_create_and_orders(client, fake_account_service):
    user = create_user("13900000011")
    headers = auth(mint_user_token(user.phone))

    res = client.post("/api/v1/payment/create", headers=headers, json={"plan": "pro", "platform": "wechat"})
    assert res.status_code == 200, res.text
    assert res.json()["order_id"] == "ord-1"
    assert res.json()["plan"] == "pro"

    orders = client.get("/api/v1/payment/orders", headers=headers)
    assert orders.status_code == 200
    assert len(orders.json()) == 1

    bad = client.post("/api/v1/payment/create", headers=headers, json={"plan": "vip"})
    assert bad.status_code == 400


def test_trial_claim_is_forwarded(client, fake_account_service):
    user = create_user("13900000014")
    headers = auth(mint_user_token(user.phone))

    claim = client.post("/api/v1/trial/claim", headers=headers, json={"phone": "13900000015"})
    assert claim.status_code == 200
    assert claim.json()["level"] == "pro"

    cards = client.get("/api/v1/trial/my-cards", headers=headers)
    assert cards.status_code == 200
    assert cards.json()["cards"] == []
