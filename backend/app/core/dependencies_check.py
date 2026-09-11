"""外部依赖连通性检查：启动时报告，健康检查时暴露状态。

设计原则：依赖不通只告警，不让应用起不来。Redis 挂掉时免费版每日额度门禁
会放行（fail-open），这是有意的取舍——限制器不该成为付费功能的可用性依赖；
但"门禁静默失效"必须让人看得见，所以启动时打印明确的 warning，
并让 /health 暴露 redis 状态供编排与监控读取。
"""
import logging
from typing import Literal

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

State = Literal["up", "down", "not_configured"]


def check_redis(timeout: float = 2.0) -> State:
    """ping 一次 Redis；任何异常都算 down，不让检查本身抛出来"""
    url = (settings.REDIS_URL or "").strip()
    if not url:
        return "not_configured"
    try:
        import redis

        client = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        try:
            client.ping()
        finally:
            client.close()
        return "up"
    except Exception as exc:  # noqa: BLE001 - 检查函数必须自吞异常
        logger.debug("redis ping failed: %s", exc)
        return "down"


def dependency_states() -> dict[str, State]:
    return {"redis": check_redis()}


def log_dependency_states() -> None:
    """启动时调用。状态不对就打 warning，日志里写清影响，方便直接 grep。"""
    states = dependency_states()

    redis_state = states["redis"]
    if redis_state == "up":
        logger.info("dependency redis: up (%s)", settings.REDIS_URL)
        return

    reason = "REDIS_URL 未配置" if redis_state == "not_configured" else "连接失败"
    logger.warning(
        "dependency redis: %s (%s)。免费版每日调用次数门禁（check_daily_call）已禁用，"
        "所有用户按不限次处理；恢复 Redis 后自动生效，无需重启。",
        redis_state,
        reason,
    )
