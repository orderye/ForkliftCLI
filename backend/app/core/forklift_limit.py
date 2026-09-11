"""叉车数据库数量限制

免费版 1 台、专业版 10 台、企业版不限。
在 add_forklift 端点创建前调用 check_forklift_quota(user, db)。
"""
from fastapi import HTTPException

from app.core.subscription_helper import effective_level, get_forklift_limit
from app.models.maintenance import UserForklift


def check_forklift_quota(user, db) -> None:
    """免费/专业版在添加前检查配额；超限 raise HTTPException(403)"""
    level = effective_level(user)
    limit = get_forklift_limit(level)
    if limit is None:
        return  # 不限（企业版）

    count = db.query(UserForklift).filter(UserForklift.user_id == user.id).count()
    if count >= limit:
        if level == "free":
            raise HTTPException(status_code=403, detail="免费版仅支持添加1台车，升级专业版可添加10台")
        raise HTTPException(status_code=403, detail="专业版最多添加10台车，请升级企业版")
