"""订阅等级的提议方案（草案，未接线）

【事实源在这里】线上等级判定与限制表在 app/core/subscription_helper.py，
等级取值是 free / pro / enterprise。业务代码请引用那个模块，不要用本模块。

本模块是一份 Air/Ultra 四档分级的设计草案，当前没有任何代码引用：
- Free：免费版，每日 3 次调用、1 台叉车
- Air：轻量版，每日 30 次调用、3 台叉车
- Pro：专业版，不限调用、10 台叉车
- Ultra：企业版（原 enterprise），不限、企业绑定 5 账户

要真正启用需要先做两件事：把 helper 里的等级字符串统一到 air/ultra 命名
（涉及数据库已有 subscription_level 值），以及让账号侧（account-service）
同步支持新档位。在那之前接入会把线上等级判定弄乱。
"""


# ── 等级常量 ──
LEVEL_FREE = "free"
LEVEL_AIR = "air"
LEVEL_PRO = "pro"
LEVEL_ULTRA = "ultra"

ALL_LEVELS = (LEVEL_FREE, LEVEL_AIR, LEVEL_PRO, LEVEL_ULTRA)
PAID_LEVELS = (LEVEL_AIR, LEVEL_PRO, LEVEL_ULTRA)

# 兼容映射：历史值/外部输入 → 新等级
LEVEL_ALIASES = {
    "enterprise": LEVEL_ULTRA,
}

# ── 限制表（未列出则不限） ──
DAILY_CALL_LIMIT = {LEVEL_FREE: 3, LEVEL_AIR: 30}
FORKLIFT_LIMIT = {LEVEL_FREE: 1, LEVEL_AIR: 3, LEVEL_PRO: 10}

# ── 价格（元） ──
PLAN_PRICES = {LEVEL_AIR: 9.0, LEVEL_PRO: 39.0, LEVEL_ULTRA: 899.0}

# ── 套餐时长（天） ──
PLAN_DURATIONS_DAYS = {LEVEL_AIR: 30, LEVEL_PRO: 30, LEVEL_ULTRA: 365}

# ── 展示信息 ──
PLAN_DISPLAY = {
    LEVEL_FREE: {"name": "免费版", "price": "¥0"},
    LEVEL_AIR: {"name": "轻量版", "price": "¥9/月"},
    LEVEL_PRO: {"name": "专业版", "price": "¥39/月"},
    LEVEL_ULTRA: {"name": "Ultra", "price": "¥899/年"},
}

# ── 企业（Ultra）相关 ──
ULTRA_MAX_ACCOUNTS = 5

# ── 体验卡 ──
TRIAL_DAYS = 7
TRIAL_GRANT_LEVEL = LEVEL_PRO  # 体验卡激活到 pro
MONTHLY_TRIAL_CARDS = {LEVEL_AIR: 1, LEVEL_PRO: 2, LEVEL_ULTRA: 10}


def normalize_level(value) -> str:
    """归一化等级字符串；None/空/未知 → free"""
    if not value:
        return LEVEL_FREE
    if value in ALL_LEVELS:
        return value
    return LEVEL_ALIASES.get(value, LEVEL_FREE)


def get_daily_limit(level: str) -> int | None:
    return DAILY_CALL_LIMIT.get(level)


def get_forklift_limit(level: str) -> int | None:
    return FORKLIFT_LIMIT.get(level)
