"""推送服务（FCM / APNs）

实现说明：
- 当前为 stub 实现：打印日志并返回成功，待接入真实 FCM/APNs SDK。
- 接入步骤：
  1. 安装 firebase-admin（FCM）或 apns2（APNs）
  2. 在 .env 配置 FIREBASE_CREDENTIALS / APNS_KEY
  3. 在 push_premium_activated / push_subscription_activated 内实现真实调用
"""
import logging

logger = logging.getLogger(__name__)


async def push_premium_activated(device_token: str) -> bool:
    """推送 7 天专业版激活通知（体验卡领取 / 企业绑定）"""
    logger.info(f"[PUSH stub] premium_activated -> {device_token}")
    # TODO: 接入 FCM / APNs
    return True


async def push_subscription_activated(device_token: str, level: str) -> bool:
    """推送订阅激活通知（支付成功）"""
    logger.info(f"[PUSH stub] subscription_activated({level}) -> {device_token}")
    return True


async def push_subscription_expired(device_token: str) -> bool:
    """推送订阅到期通知（降级为 free）"""
    logger.info(f"[PUSH stub] subscription_expired -> {device_token}")
    return True
