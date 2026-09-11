"""订阅等级常量与配置 — 单一事实源

所有等级字符串、限制、价格、时长集中在此模块。
业务代码应引用本模块的常量，不再硬编码等级字符串。

等级体系：Free / Air / Pro / Ultra
- Free：免费版，每日 3 次调用、1 台叉车
- Air：轻量版，每日 30 次调用、3 台叉车
- Pro：专业版，不限调用、10 台叉车
- Ultra：企业版（原 enterprise），不限、企业绑定 5 账户
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
