"""account-service 客户端 — 薄壳：注入本项目配置，实现在 forklift_shared。

所有认证、订阅、支付、企业、体验卡、后台管理请求都转发到 account-service。
ForkliftCLI 本地仅保留用户投影（users 表），用于业务关联与等级门禁。
"""
from forklift_shared import account_client as _shared

from app.config import get_settings

_shared.configure(get_settings().ACCOUNT_SERVICE_URL)

post = _shared.post
get = _shared.get
put = _shared.put
delete = _shared.delete
