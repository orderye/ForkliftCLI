"""订阅门禁 / 配额 / 速率限制 的端到端与机制测试"""
import pytest

from conftest import create_user, mint_user_token


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def model_id(catalog):
    return catalog["model_id"]


# ========== 叉车数量配额（真实端点） ==========


def _add(client, headers, model_id, serial):
    return client.post("/api/v1/my-forklifts", headers=headers, json={"forklift_model_id": model_id, "serial_number": serial})


def test_free_user_quota_is_one(client, model_id):
    headers = auth(mint_user_token(create_user("13700000001").phone))
    assert _add(client, headers, model_id, "A1").status_code == 200
    second = _add(client, headers, model_id, "A2")
    assert second.status_code == 403
    assert "免费版" in second.text

    # 删掉一台后可以再加
    forklift_id = client.get("/api/v1/my-forklifts", headers=headers).json()[0]["id"]
    client.delete(f"/api/v1/my-forklifts/{forklift_id}", headers=headers)
    assert _add(client, headers, model_id, "A3").status_code == 200


def test_pro_user_quota_is_ten(client, model_id):
    headers = auth(mint_user_token(create_user("13700000002", level="pro", expires_in_days=30).phone))
    for i in range(3):
        assert _add(client, headers, model_id, f"P{i}").status_code == 200
    assert len(client.get("/api/v1/my-forklifts", headers=headers).json()) == 3


def test_enterprise_user_has_no_limit(client, model_id):
    from app.core.database import SessionLocal
    from app.models.enterprise import Enterprise

    db = SessionLocal()
    try:
        ent = Enterprise(name="集团测试", code="GTEST-001", plan="enterprise")
        db.add(ent)
        db.commit()
        db.refresh(ent)
        enterprise_id = ent.id
    finally:
        db.close()

    user = create_user("13700000003", level="enterprise", expires_in_days=365, enterprise_id=enterprise_id)
    headers = auth(mint_user_token(user.phone))
    for i in range(3):
        assert _add(client, headers, model_id, f"E{i}").status_code == 200


# ========== 等级判定 ==========


def test_effective_level_matrix():
    from app.core.subscription_helper import effective_level
    from datetime import datetime, timedelta, timezone
    from app.models.user import User

    def mk(**kw):
        user = User(phone="x", enterprise_obj=None)  # 显式置空，避免脱离会话后触发懒加载
        for key, value in kw.items():
            setattr(user, key, value)
        return user

    assert effective_level(mk()) == "free"
    assert effective_level(mk(subscription_level="pro", subscription_expires_at=None)) == "pro"
    assert effective_level(
        mk(subscription_level="pro", subscription_expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    ) == "free"
    assert effective_level(
        mk(subscription_level="pro", subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    ) == "pro"


def test_limit_maps_are_complete():
    from app.core.subscription_helper import get_daily_limit, get_forklift_limit

    assert get_daily_limit("free") == 3
    assert get_daily_limit("pro") is None
    assert get_daily_limit("enterprise") is None
    assert get_forklift_limit("free") == 1
    assert get_forklift_limit("pro") == 10
    assert get_forklift_limit("enterprise") is None


# ========== 每日调用次数限制（免费版 3 次/功能） ==========


def test_daily_limit_blocks_on_fourth_call(fake_redis):
    from fastapi import HTTPException
    from app.core.rate_limit import check_daily_call

    user = create_user("13700000004")
    for _ in range(3):
        check_daily_call(user.id, "ai_chat")

    with pytest.raises(HTTPException) as exc:
        check_daily_call(user.id, "ai_chat")
    assert exc.value.status_code == 429
    assert "免费额度" in exc.value.detail


def test_daily_limit_is_scoped_per_feature(fake_redis):
    from app.core.rate_limit import check_daily_call

    user = create_user("13700000005")
    for _ in range(3):
        check_daily_call(user.id, "ai_chat")
    # 另一个功能仍有额度
    check_daily_call(user.id, "ocr")


def test_daily_limit_bypassed_for_paid_users(fake_redis):
    from app.core.rate_limit import check_daily_call

    user = create_user("13700000006", level="pro", expires_in_days=30)
    for _ in range(20):
        check_daily_call(user.id, "ai_chat")  # 专业版不限次，不应抛 429


def test_daily_limit_key_shape_is_ttl_based(fake_redis):
    from app.core.rate_limit import check_daily_call

    user = create_user("13700000007")
    check_daily_call(user.id, "ocr")
    key = next(iter(fake_redis.store))
    assert key.startswith(f"user:{user.id}:daily:ocr:")
    assert len(key.split(":")) == 5  # user:{uid}:daily:{feature}:{YYYYMMDD}


# ========== 速率限制是否真的接入端点 ==========

# 这些功能会调用外部 LLM / 向量模型，是免费版每日 3 次门禁的落点。
# 集合是刻意固定的：删掉任何一个接入点都会让这份断言失败。
EXPECTED_RATE_LIMITED_FEATURES = {
    "ai_chat",
    "ai_diagnose",
    "ocr",
    "embed",
    "embed_search",
    "manual_search",
}


def _wired_features() -> set[str]:
    import re
    from pathlib import Path

    api_dir = Path(__file__).resolve().parent.parent / "app" / "api"
    features: set[str] = set()
    for path in api_dir.rglob("*.py"):
        features |= set(re.findall(r'check_daily_call\([^,]+,\s*"([^"]+)"', path.read_text(encoding="utf-8")))
    return features


def test_rate_limit_covers_all_paid_ai_endpoints():
    """每个高成本功能都必须接上免费额度门禁，漏接一个就少收一份钱。"""
    assert _wired_features() == EXPECTED_RATE_LIMITED_FEATURES


def test_daily_limit_blocks_the_fourth_embed_call(client, fake_redis, monkeypatch):
    """走真实路由：免费用户连续调用 4 次，第 4 次必须 429"""
    import app.api.embed as embed_api

    monkeypatch.setattr(embed_api, "get_text_embedding", lambda _text: [0.01] * 384)

    user = create_user("13700000010")
    headers = auth(mint_user_token(user.phone))
    payload = {"text": "举升无力"}

    for i in range(3):
        resp = client.post("/api/v1/embed", headers=headers, json=payload)
        assert resp.status_code == 200, (i, resp.text)

    blocked = client.post("/api/v1/embed", headers=headers, json=payload)
    assert blocked.status_code == 429
    assert "免费额度" in blocked.text

    # 另一个功能仍有余量，说明门禁按 feature 分桶
    assert client.post("/api/v1/embed/search", headers=headers, json={"query_text": "故障灯"}).status_code == 200


def test_paid_user_is_not_rate_limited(client, fake_redis, monkeypatch):
    import app.api.embed as embed_api

    monkeypatch.setattr(embed_api, "get_text_embedding", lambda _text: [0.01] * 384)

    user = create_user("13700000011", level="pro", expires_in_days=30)
    headers = auth(mint_user_token(user.phone))
    for _ in range(10):
        assert client.post("/api/v1/embed", headers=headers, json={"text": "检修"}).status_code == 200


def test_daily_limit_fails_open_when_redis_is_down(client, monkeypatch):
    """Redis 挂掉时放行而不是把付费功能一起打挂（fail-open）"""
    import app.api.embed as embed_api
    import app.core.rate_limit as rate_limit

    monkeypatch.setattr(embed_api, "get_text_embedding", lambda _text: [0.01] * 384)
    monkeypatch.setattr(rate_limit, "_get_redis", lambda: (_ for _ in ()).throw(ConnectionError("redis down")))

    user = create_user("13700000012")
    headers = auth(mint_user_token(user.phone))
    for _ in range(5):
        assert client.post("/api/v1/embed", headers=headers, json={"text": "x"}).status_code == 200

    # 订阅过期用户会被 effective_level 降级为 free，但 Redis 故障时同样放行
    from app.models.user import User
    from app.core.database import SessionLocal
    from datetime import datetime, timedelta, timezone

    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user.id).update(
            {"subscription_level": "pro", "subscription_expires_at": datetime.now(timezone.utc) - timedelta(days=1)}
        )
        db.commit()
    finally:
        db.close()
    assert client.post("/api/v1/embed", headers=headers, json={"text": "x"}).status_code == 200
