"""订阅等级常量 — 薄壳：单一事实源在 forklift_shared.subscription_levels。

历史说明：本模块曾是 ForkliftCLI 3 级（free/pro/enterprise）时代的四档草案，
现已随 account-system 四级体系（free/air/pro/ultra）全面接线；等级判定事实源
在 forklift_shared.subscription_helper（本项目 app/core/subscription_helper.py
为注入本项目模型的薄壳）。
"""
from forklift_shared.subscription_levels import *  # noqa: F401,F403
from forklift_shared import subscription_levels as _src

# 显式列出常用名，便于 IDE 跳转与静态检查
LEVEL_FREE = _src.LEVEL_FREE
LEVEL_AIR = _src.LEVEL_AIR
LEVEL_PRO = _src.LEVEL_PRO
LEVEL_ULTRA = _src.LEVEL_ULTRA
ALL_LEVELS = _src.ALL_LEVELS
PAID_LEVELS = _src.PAID_LEVELS
normalize_level = _src.normalize_level
get_daily_limit = _src.get_daily_limit
get_forklift_limit = _src.get_forklift_limit
