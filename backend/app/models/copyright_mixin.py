"""版权合规字段 Mixin（MASTER_PLAN 4.3 版权合规）

source 由各表按需自行定义（命名/长度可能不同），Mixin 只包含其余 4 列：
copyright_owner / license_type / license_expire / commercial_use
"""
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Integer, or_

# 授权类型白名单
LICENSE_TYPES = {
    "self_owned",                # 自研/自制
    "licensed",                  # 商业授权（供应商合同）
    "cc0", "cc_by", "cc_by_sa",  # 开源协议
    "public_domain",             # 公有领域
    "user_uploaded",             # 用户上传（责任归上传者）
    "internal_only",             # 仅内部使用
}

# 不可标记为可商用的授权类型
NON_COMMERCIAL_LICENSES = {"user_uploaded", "internal_only"}


def as_naive_utc(dt: datetime) -> datetime:
    """统一转为 naive UTC（与库内 DateTime 列一致）"""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def naive_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_license_expired(expire: datetime | None) -> bool:
    """授权是否已到期（NULL = 永久授权）"""
    if expire is None:
        return False
    return as_naive_utc(expire) < naive_utc_now()


def license_active_condition(column):
    """SQLAlchemy 过滤条件：授权有效（expire 为 NULL 或晚于当前时间）"""
    return or_(column.is_(None), column > naive_utc_now())


class CopyrightMixin:
    copyright_owner = Column(String(200), default="")
    license_type = Column(String(30), default="self_owned", nullable=False)
    license_expire = Column(DateTime, nullable=True)               # NULL = 永久授权
    commercial_use = Column(Integer, default=0, nullable=False)    # 0/1

    @property
    def license_expired(self) -> bool:
        return is_license_expired(self.license_expire)
