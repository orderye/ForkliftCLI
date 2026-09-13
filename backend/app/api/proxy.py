"""账户类路由代理 — 薄壳：转发工厂实现在 forklift_shared.proxy。

account-service 才是账户权威（认证/订阅/支付/企业/体验卡/后台）。
ForkliftCLI 只负责转发，避免双库逻辑漂移。
"""
from forklift_shared.proxy import build_proxy_routers

from app.config import get_settings
from app.core.security import oauth2_scheme

settings = get_settings()
BASE = settings.ACCOUNT_SERVICE_URL.rstrip("/")

# 需要代理转发的账户类前缀
PROXY_PREFIXES = [
    "/subscription",
    "/payment",
    "/enterprise",
    "/trial",
    "/public",
]

routers = build_proxy_routers(
    prefixes=PROXY_PREFIXES,
    base_url_getter=lambda: BASE,
    scheme=oauth2_scheme,
    tag_prefix="代理",
)
