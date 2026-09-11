"""E2E 测试公共设施

关键设计：测试库不是 Base.metadata.create_all 建的，而是真跑 alembic 迁移链
（等价于全新安装），这样「模型改了但迁移没跟上」或「迁移顺序有坑」的问题
会在测试里立刻暴露，而不是等部署才发现。

注意：DATABASE_URL 必须在导入 app.* 之前设置 —— app.config.get_settings() 带 lru_cache，
导入顺序错了会读到默认的 ./forklift_bao.db。
"""
import json
import os
import shutil
import sys
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_TMP_DIR = Path(tempfile.mkdtemp(prefix="forkliftcli-e2e-"))
DB_PATH = _TMP_DIR / "e2e.db"

os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["USE_MEMORY_STORE"] = "true"
os.environ["DEBUG"] = "false"
os.environ["AI_API_KEY"] = ""
# 存储客户端在导入 app 时就实例化，上传目录必须指向临时目录，别写进仓库
os.environ["UPLOAD_DIR"] = str(_TMP_DIR / "uploads")


def run_alembic(db_url: str, target: str = "head"):
    from alembic.config import Config
    from alembic import command

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, target)


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """整个测试会话共用一个真跑过迁移链的库"""
    run_alembic(f"sqlite:///{DB_PATH}")
    yield DB_PATH
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture(scope="session")
def client(migrated_database):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def mint_user_token(phone: str, extra: dict | None = None) -> str:
    """用户令牌：payload.sub 必须是 users.phone"""
    from app.core.security import create_access_token

    payload = {"sub": phone}
    if extra:
        payload.update(extra)
    return create_access_token(payload)


def mint_admin_token(phone: str = "13800000000", role: str = "super_admin") -> str:
    """管理员令牌用派生密钥，与用户令牌严格隔离"""
    from jose import jwt
    from app.config import get_settings

    s = get_settings()
    payload = {
        "sub": phone,
        "role": role,
        "type": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, s.SECRET_KEY + ":admin", algorithm=s.ALGORITHM)


def create_user(
    phone: str,
    level: str = "free",
    expires_in_days: int | None = None,
    nickname: str = "",
    enterprise_id: int | None = None,
):
    """在本地投影表里造一个真实用户"""
    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        user = User(
            phone=phone,
            nickname=nickname or f"user-{phone[-4:]}",
            subscription_level=level,
            subscription_expires_at=(
                datetime.now(timezone.utc) + timedelta(days=expires_in_days)
                if expires_in_days is not None
                else None
            ),
            enterprise_id=enterprise_id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="session")
def catalog(migrated_database):
    """车型 / 发动机 / 配件目录，供需要真实外键的接口使用"""
    from app.core.database import SessionLocal
    from app.models.forklift import ForkliftBrand, ForkliftSeries, ForkliftModel
    from app.models.engine import EngineBrand, EngineModel
    from app.models.part import Part, PartOem

    db = SessionLocal()
    try:
        brand = ForkliftBrand(name="测试品牌", name_en="TEST", country="CN")
        db.add(brand)
        db.flush()

        engine_brand = EngineBrand(name="测试发动机品牌", name_en="TEST-ENG")
        db.add(engine_brand)
        db.flush()

        engine_model = EngineModel(
            brand_id=engine_brand.id,
            model_name="TE-100",
            displacement="2.0",
            power_kw=55,
        )
        db.add(engine_model)
        db.flush()

        series = ForkliftSeries(brand_id=brand.id, name="测试系列")
        db.add(series)
        db.flush()

        model = ForkliftModel(
            series_id=series.id,
            name="TEST-3T",
            load_capacity_kg=3000,
            lift_height_mm=3000,
            fuel_type="diesel",
            engine_model_id=engine_model.id,
        )
        db.add(model)
        db.flush()

        part = Part(
            name="测试液压泵",
            oem_number="TP-0001",
            category="hydraulic",
            brand="测试品牌",
            price_reference=1280.0,
        )
        db.add(part)
        db.flush()
        db.add(PartOem(part_id=part.id, oem_number="TP-0001", manufacturer="测试品牌"))

        db.commit()
        return {
            "brand_id": brand.id,
            "engine_brand_id": engine_brand.id,
            "engine_model_id": engine_model.id,
            "series_id": series.id,
            "model_id": model.id,
            "part_id": part.id,
        }
    finally:
        db.close()


class FakeRedis:
    """最小 Redis 替身：只实现 check_daily_call 用到的 get/incr/expire/pipeline"""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def incr(self, key):
        self.store[key] = str(int(self.store.get(key, "0")) + 1)
        return self.store[key]

    def expire(self, key, ttl):
        return True

    def pipeline(self):
        return self

    def execute(self):
        return []


@pytest.fixture()
def fake_redis(monkeypatch):
    """把 rate_limit 的 Redis 换成内存替身，让 429 门禁可离线验证"""
    import app.core.rate_limit as rate_limit

    fake = FakeRedis()
    monkeypatch.setattr(rate_limit, "_get_redis", lambda: fake)
    return fake


class _FakeAccountServiceHandler(BaseHTTPRequestHandler):
    """本地假的 account-service：按契约返回响应，并记录收到的请求头。

    订阅 / 支付 / 企业 / 体验卡 / 用户管理都是转发到 account-service 的，
    离线测试时用它替代真实服务，验证「转发链路是否正确、令牌是否透传」。
    """

    svc: "_FakeAccountService"

    def log_message(self, *args):
        pass

    def _record(self):
        self.svc.last_method = self.command
        self.svc.last_path = self.path
        self.svc.last_authorization = self.headers.get("Authorization", "")
        length = int(self.headers.get("Content-Length") or 0)
        self.svc.last_body = json.loads(self.rfile.read(length)) if length else None

    def _reply(self, status: int = 200, payload=None):
        body = json.dumps(payload or {}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        self._record()
        path = self.path.split("?", 1)[0]
        body = self.svc.last_body or {}

        if path == "/api/v1/subscription/me":
            return self._reply(200, {
                "level": "pro", "expires_at": "2026-12-31T23:59:59",
                "enterprise_id": None, "enterprise_name": "", "trial_cards_remaining": 2,
            })
        if path in ("/api/v1/subscription/activate", "/api/v1/subscription/renew"):
            if body.get("plan") not in ("pro", "enterprise"):
                return self._reply(400, {"detail": "非法套餐"})
            return self._reply(200, {"level": body["plan"], "expires_at": "2026-12-31T23:59:59"})
        if path == "/api/v1/subscription/cancel":
            return self._reply(200, {"cancelled": True})

        if path == "/api/v1/enterprise/bind_account":
            phone = body.get("phone_number", "")
            if phone.startswith("13900001006"):
                return self._reply(403, {"detail": "企业最多绑定 5 个账户"})
            self.svc.bind_count += 1
            return self._reply(200, {"bound": True, "account_count": self.svc.bind_count})
        if path == "/api/v1/enterprise/unbind_account":
            return self._reply(200, {"unbound": True, "account_count": 0})
        if path == "/api/v1/enterprise/accounts":
            return self._reply(200, {"accounts": [], "account_count": self.svc.bind_count})
        if path == "/api/v1/enterprise/create":
            return self._reply(200, {"enterprise_id": 1, "name": body.get("name", "")})

        if path == "/api/v1/payment/create":
            if body.get("plan") not in ("pro", "enterprise"):
                return self._reply(400, {"detail": "非法套餐"})
            self.svc.orders.append({"order_id": "ord-1", "plan": body["plan"]})
            return self._reply(200, {"order_id": "ord-1", "plan": body["plan"], "payment_params": {"qr": "x"}})
        if path == "/api/v1/payment/orders":
            return self._reply(200, self.svc.orders)
        if path == "/api/v1/payment/notify":
            return self._reply(200, {"ok": True})

        if path == "/api/v1/trial/claim":
            return self._reply(200, {"activated": True, "level": "pro"})
        if path == "/api/v1/trial/my-cards":
            return self._reply(200, {"cards": []})

        if path in ("/api/v1/auth/register", "/api/v1/auth/login"):
            phone = body.get("phone", "13999999999")
            return self._reply(200, {
                "access_token": "user-token",
                "user": {"id": 1, "phone": phone, "email": "", "nickname": "", "avatar": "",
                         "subscription_level": "free", "subscription_expires_at": None,
                         "is_active": True, "last_login_at": None},
            })
        if path in ("/api/v1/admin/auth/register", "/api/v1/admin/auth/login"):
            phone = body.get("phone", "13800000000")
            return self._reply(200, {
                "access_token": "admin-token",
                "user": {"id": 2, "phone": phone, "role": "super_admin", "is_super_admin": True},
            })

        if path == "/api/v1/admin/users":
            return self._reply(200, {"items": [], "total": 0, "page": 1, "page_size": 20})

        # 看板聚合依赖的账户维度统计接口
        if path == "/api/v1/admin/users/stats/by-level":
            return self._reply(200, {"free": 1, "pro": 0, "enterprise": 0, "total": 1})
        if path == "/api/v1/admin/enterprises/stats":
            return self._reply(200, {"total": 0, "active": 0, "members": 0})
        if path == "/api/v1/admin/payments/stats":
            return self._reply(200, {"total_amount": 0, "total_orders": 0, "by_plan": {}})
        if path == "/api/v1/admin/trial/stats":
            return self._reply(200, {"issued": 0, "activated": 0, "remaining": 0})
        if path == "/api/v1/admin/subscription/stats/overview":
            return self._reply(200, {"active": 0, "expired": 0, "converting": 0})

        return self._reply(404, {"detail": f"fake account-service: 未实现 {path}"})

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_DELETE = _handle
    do_PATCH = _handle


class _FakeAccountService:
    def __init__(self, port: int):
        # proxy 会在 BASE 后拼接 /{prefix}/{path}，BASE 必须带上 /api/v1
        self.base_url = f"http://127.0.0.1:{port}/api/v1"
        self.last_method = None
        self.last_path = None
        self.last_authorization = ""
        self.last_body = None
        self.bind_count = 0
        self.orders = []
        handler = type("Handler", (_FakeAccountServiceHandler,), {})
        handler.svc = self
        self._httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=5)


@pytest.fixture()
def fake_account_service(monkeypatch):
    """把 account_client 与 proxy 的 BASE 指到本地假服务"""
    import app.api.proxy as proxy_module
    import app.core.account_client as account_client

    port = _next_port()
    service = _FakeAccountService(port)
    try:
        monkeypatch.setattr(account_client, "BASE", service.base_url)
        monkeypatch.setattr(proxy_module, "BASE", service.base_url)
        yield service
    finally:
        service.stop()


def _next_port() -> int:
    global _PORT
    _PORT += 1
    return _PORT


_PORT = 45700
