"""账户相关路由代理：将 ForkliftCLI 的账户类请求透明转发到 account-service。

account-service 才是账户权威（认证/订阅/支付/企业/体验卡/后台）。
ForkliftCLI 只负责转发，避免双库逻辑漂移。
"""
import httpx
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

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


def _make_router(prefix: str) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[f"代理 {prefix}"])

    @router.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        include_in_schema=False,
    )
    async def forward(
        path: str,
        request: Request,
        token: str = Depends(oauth2_scheme),
    ):
        url = f"{BASE}{prefix}/{path}"
        headers = dict(request.headers)
        # 用 account-service 的 token 替换本地 Bearer
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            headers.pop("Authorization", None)
        body = await request.body()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                params=request.query_params,
                content=body,
            )
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return JSONResponse(status_code=resp.status_code, content=data)

    return router


routers = [_make_router(prefix) for prefix in PROXY_PREFIXES]
