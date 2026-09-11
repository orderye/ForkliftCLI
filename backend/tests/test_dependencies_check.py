"""外部依赖连通性检查的测试

门禁静默失效比门禁不生效更糟：Redis 挂掉时免费版额度门禁会 fail-open，
这个事实必须能被日志和 /health 看到，所以上报逻辑本身要可测。
"""
from app.core import dependencies_check


class _RecordingLogger:
    """记录调用即可。不用 caplog：迁移测试会用 alembic 的 fileConfig 重置 root 日志配置，
    pytest 挂在 root 上的 handler 会被摘掉，导致 caplog 收不到记录。"""

    def __init__(self, calls):
        self.calls = calls

    def _log(self, level):
        def call(fmt, *args):
            try:
                message = fmt % args if args else fmt
            except Exception:
                message = " ".join(map(str, (fmt,) + args))
            self.calls.append({"level": level, "message": message})

        return call

    def warning(self, *args):
        return self._log("warning")(*args)

    def info(self, *args):
        return self._log("info")(*args)

    def debug(self, *args):
        return self._log("debug")(*args)

    def error(self, *args):
        return self._log("error")(*args)


def _capture_logs(monkeypatch):
    calls = []
    monkeypatch.setattr(dependencies_check, "logger", _RecordingLogger(calls))
    return calls


def test_not_configured_when_url_empty(monkeypatch):
    monkeypatch.setattr(dependencies_check.settings, "REDIS_URL", "")
    assert dependencies_check.check_redis() == "not_configured"


def test_connection_failure_reports_down_not_exception(monkeypatch):
    """检查函数必须自吞异常，不能因为探测失败让整个进程起不来"""
    monkeypatch.setattr(dependencies_check.settings, "REDIS_URL", "redis://127.0.0.1:1/0")
    assert dependencies_check.check_redis(timeout=0.1) == "down"


def test_successful_ping_reports_up(monkeypatch):
    class _Client:
        def ping(self):
            return True

        def close(self):
            pass

    monkeypatch.setattr(dependencies_check.settings, "REDIS_URL", "redis://x/0")
    monkeypatch.setattr("redis.from_url", lambda *a, **kw: _Client())
    assert dependencies_check.check_redis() == "up"


def test_dependency_states_exposes_redis():
    states = dependencies_check.dependency_states()
    assert set(states) == {"redis"}
    assert states["redis"] in {"up", "down", "not_configured"}


def test_log_down_emits_warning_naming_the_disabled_gate(monkeypatch):
    """告警文案必须点明受影响的功能，运维照着 grep 就能定位"""
    calls = _capture_logs(monkeypatch)
    monkeypatch.setattr(dependencies_check, "check_redis", lambda timeout=2.0: "down")

    dependencies_check.log_dependency_states()

    warnings = [c for c in calls if c["level"] == "warning"]
    assert warnings, "Redis 不通时必须打 warning，否则门禁失效没人看得见"
    text = " ".join(c["message"] for c in warnings)
    assert "dependency redis: down" in text
    assert "check_daily_call" in text


def test_log_up_is_info_only(monkeypatch):
    calls = _capture_logs(monkeypatch)
    monkeypatch.setattr(dependencies_check, "check_redis", lambda timeout=2.0: "up")

    dependencies_check.log_dependency_states()

    assert all(c["level"] != "warning" for c in calls)
