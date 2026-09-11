"""account-service 客户端：账户权威服务的 HTTP 调用封装。

所有认证、订阅、支付、企业、体验卡、后台管理请求都转发到 account-service。
ForkliftCLI 本地仅保留用户投影（users 表），用于业务关联与等级门禁。
"""
from typing import Any, Optional

import httpx

from app.config import get_settings

settings = get_settings()
BASE = settings.ACCOUNT_SERVICE_URL.rstrip("/")


def _headers(token: Optional[str] = None) -> dict:
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def post(path: str, *, json: dict, token: Optional[str] = None, timeout: float = 10.0) -> dict:
    resp = httpx.post(f"{BASE}{path}", json=json, headers=_headers(token), timeout=timeout)
    return _parse(resp)


def get(path: str, *, token: Optional[str] = None, params: Optional[dict] = None, timeout: float = 10.0) -> dict:
    resp = httpx.get(f"{BASE}{path}", headers=_headers(token), params=params, timeout=timeout)
    return _parse(resp)


def put(path: str, *, json: dict, token: Optional[str] = None, timeout: float = 10.0) -> dict:
    resp = httpx.put(f"{BASE}{path}", json=json, headers=_headers(token), timeout=timeout)
    return _parse(resp)


def delete(path: str, *, token: Optional[str] = None, timeout: float = 10.0) -> dict:
    resp = httpx.delete(f"{BASE}{path}", headers=_headers(token), timeout=timeout)
    return _parse(resp)


def _parse(resp: httpx.Response) -> Any:
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    if resp.status_code >= 400:
        detail = data.get("detail") if isinstance(data, dict) else str(data)
        from fastapi import HTTPException
        raise HTTPException(status_code=resp.status_code, detail=detail or "账户服务调用失败")
    return data
