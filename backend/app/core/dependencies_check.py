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


def check_qdrant(timeout: float = 2.0) -> State:
    """get_collections 一次验证 Qdrant 连通性；内存存储模式下视为 not_configured"""
    if settings.USE_MEMORY_STORE:
        return "not_configured"
    url = (settings.QDRANT_URL or "").strip()
    if not url:
        return "not_configured"
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=url, timeout=timeout)
        try:
            client.get_collections()
        finally:
            client.close()
        return "up"
    except Exception as exc:  # noqa: BLE001 - 检查函数必须自吞异常
        logger.debug("qdrant ping failed: %s", exc)
        return "down"


def check_wemm(timeout: float = 2.0) -> State:
    """只校验 WeMM 配置合法性，不加载模型（健康检查不能触发重模型下载）"""
    if not (settings.WEMM_MODEL_NAME or "").strip():
        return "not_configured"
    try:
        from app.services.embedding_service import SUPPORTED_DIMS_2B

        if int(settings.WEMM_EMBED_DIM) not in SUPPORTED_DIMS_2B:
            return "down"
    except Exception as exc:  # noqa: BLE001
        logger.debug("wemm config check failed: %s", exc)
        return "down"
    return "up"


def dependency_states() -> dict[str, State]:
    return {
        "redis": check_redis(),
        "qdrant": check_qdrant(),
        "wemm": check_wemm(),
    }


def log_dependency_states() -> None:
    """启动时调用。状态不对就打 warning，日志里写清影响，方便直接 grep。"""
    states = dependency_states()

    redis_state = states["redis"]
    if redis_state == "up":
        logger.info("dependency redis: up (%s)", settings.REDIS_URL)
    elif redis_state == "not_configured":
        logger.warning(
            "dependency redis: not_configured。免费版每日调用次数门禁（check_daily_call）已禁用，"
            "所有用户按不限次处理；恢复 Redis 后自动生效，无需重启。"
        )
    else:
        logger.warning(
            "dependency redis: down (%s)。免费版每日调用次数门禁（check_daily_call）已禁用，"
            "所有用户按不限次处理；恢复 Redis 后自动生效，无需重启。",
            settings.REDIS_URL,
        )

    qdrant_state = states["qdrant"]
    if qdrant_state == "up":
        logger.info("dependency qdrant: up (%s)", settings.QDRANT_URL)
    elif qdrant_state == "not_configured":
        logger.info(
            "dependency qdrant: not_configured (USE_MEMORY_STORE=%s，向量仅存于进程内存)",
            settings.USE_MEMORY_STORE,
        )
    else:
        logger.warning(
            "dependency qdrant: down (%s)。WeMM 向量召回不可用，"
            "AI 检索将退化为 BM25+MiniLM 混合召回。",
            settings.QDRANT_URL,
        )

    wemm_state = states["wemm"]
    if wemm_state == "up":
        logger.info(
            "dependency wemm: up (model=%s dim=%s device=%s)",
            settings.WEMM_MODEL_NAME,
            settings.WEMM_EMBED_DIM,
            settings.WEMM_DEVICE,
        )
    else:
        logger.warning(
            "dependency wemm: %s。多模态向量召回与 embedding 接口不可用。",
            wemm_state,
        )
