"""架构不变量：把靠约定维持的接线状态固化成断言。

这里全是静态检查（读源码），不建库、不起服务，跑一次只要几十毫秒。
目的是挡住两类回归：
1. 有人把 proxy 前缀下的本地实现重新注册进 main，两套逻辑同时生效；
2. proxy 的转发前缀被改，账户请求悄悄落到本地而不是 account-service。

真正的转发行为（HTTP 是否真的打到 account-service）由
tests/test_e2e_api.py::test_subscription_is_forwarded_to_account_service 覆盖。
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"

# proxy 独占的账户类前缀，与 app/api/proxy.py 的 PROXY_PREFIXES 对应
ACCOUNT_PROXIED_PREFIXES = ("/subscription", "/payment", "/enterprise", "/trial")


def _walk_routes(routes: list, acc: list) -> list:
    """递归收集路由 path。FastAPI 把 include_router 的结果包在 _IncludedRouter 里，
    直接遍历 app.routes 会漏掉所有子路由。"""
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            _walk_routes(getattr(original, "routes", []) or [], acc)
        else:
            path = getattr(route, "path", None)
            if path:
                acc.append(path)
    return acc


def test_proxy_wildcard_registered_for_each_account_prefix():
    """每个账户前缀都必须有一个通配转发路由，本地实现不允许接管"""
    import app.api.proxy as proxy_module
    from app.main import app

    assert tuple(proxy_module.PROXY_PREFIXES) == (*ACCOUNT_PROXIED_PREFIXES, "/public")

    paths = _walk_routes(app.routes, [])
    for prefix in ACCOUNT_PROXIED_PREFIXES:
        expected = f"{prefix}/{{path:path}}"
        assert expected in paths, f"{prefix} 缺少通配转发路由 {expected}，账户请求不会被代理"


def test_no_local_router_registered_for_proxied_prefixes():
    """同前缀的本地实现可以留在仓库里当参考，但不能进 main.py"""
    main_src = (APP_DIR / "main.py").read_text(encoding="utf-8")
    imported = {node.module for node in ast.walk(ast.parse(main_src)) if isinstance(node, ast.ImportFrom)}

    for prefix in ACCOUNT_PROXIED_PREFIXES:
        module_name = prefix.strip("/")
        module_file = APP_DIR / "api" / f"{module_name}.py"
        assert module_file.exists(), f"缺少参考实现 api/{module_name}.py"

        local_router = [
            node
            for node in ast.walk(ast.parse(module_file.read_text(encoding="utf-8")))
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "router" for t in node.targets)
        ]
        assert local_router, f"api/{module_name}.py 里没有 router，参考实现已失效"

        assert f"app.api.{module_name}" not in imported, (
            f"app/api/{module_name}.py 被注册进 main.py，会与 proxy 的 {prefix} 转发路由冲突；"
            f"账户权威在 account-service"
        )


def test_subscription_helper_is_the_live_level_source():
    """等级判定的事实源只能是 subscription_helper，草案模块不能反客为主"""
    helper_src = (APP_DIR / "core" / "subscription_helper.py").read_text(encoding="utf-8")
    draft_src = (APP_DIR / "core" / "subscription_levels.py").read_text(encoding="utf-8")

    assert "def effective_level" in helper_src and "get_daily_limit" in helper_src
    assert "subscription_levels" not in helper_src, "事实源模块不应该依赖草案模块"
    assert "subscription_helper" in draft_src, "草案模块必须写明事实源在 subscription_helper"


def test_rate_limited_features_match_the_declared_set():
    """免费版每日额度门禁的落点集合是刻意固定的，改集合要同步改测试"""
    limits_src = (ROOT / "tests" / "test_e2e_limits.py").read_text(encoding="utf-8")
    declared = set(re.findall(r'"([a-z_]+)"', re.search(
        r"EXPECTED_RATE_LIMITED_FEATURES\s*=\s*\{(.*?)\}", limits_src, re.S
    ).group(1)))

    features: set[str] = set()
    for path in (APP_DIR / "api").rglob("*.py"):
        features |= set(re.findall(r'check_daily_call\([^,]+,\s*"([^"]+)"', path.read_text(encoding="utf-8")))
    assert features == declared, f"端点实际接入 {sorted(features)}，声明 {sorted(declared)}"
