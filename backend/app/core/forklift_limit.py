"""叉车档案数量配额 — 薄壳：实现在 forklift_shared.forklift_limit。

免费版 1 台、Air 版 3 台、专业版 10 台、Ultra（企业）不限。
在 add_forklift 端点创建前调用 check_forklift_quota(user, db)。
"""
from forklift_shared.forklift_limit import check_forklift_quota as _shared_check


def _count_user_forklifts(user_id: int, db) -> int:
    from app.models.maintenance import UserForklift

    return db.query(UserForklift).filter(UserForklift.user_id == user_id).count()


def check_forklift_quota(user, db) -> None:
    """免费/Air/专业版在添加前检查配额；超限 raise HTTPException(403)"""
    _shared_check(user, db, _count_user_forklifts)
