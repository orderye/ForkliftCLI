"""后台-数据看板（汇总统计）。

用户/订阅/支付/企业/体验卡等账户维度统计均由 account-service 管理。
ForkliftCLI 仅做代理聚合，避免双库统计漂移。
"""
from fastapi import APIRouter, Depends

from app.core.account_client import get as acct_get
from app.core.admin_auth import require_admin, AdminPrincipal
from app.core.database import get_db
from app.core.error_handler import safe_api
from app.models.ai import FaultCode, FaultTree, KnowledgeDocument
from app.models.diagram import Diagram
from app.models.engine import EngineBrand, EngineModel
from app.models.forklift import ForkliftBrand, ForkliftModel, ForkliftSeries
from app.models.maintenance import MaintenanceRecord, MaintenanceReminder, UserForklift
from app.models.model3d import Model3D
from app.models.part import Part

router = APIRouter(prefix="/admin/dashboard", tags=["后台-数据看板"])


@router.get("/stats")
@safe_api
def stats(
    db=Depends(get_db),
    admin: AdminPrincipal = Depends(require_admin),
):
    """看板统计：catalog/ai/maintenance 由 ForkliftCLI 本地统计，用户/账户维度由 account-service 提供。"""
    token = admin.token if hasattr(admin, "token") else None
    user_stats = acct_get("/admin/users/stats/by-level", token=token)
    enterprise_stats = acct_get("/admin/enterprises/stats", token=token)
    payment_stats = acct_get("/admin/payments/stats", token=token)
    trial_stats = acct_get("/admin/trial/stats", token=token)
    subscription_stats = acct_get("/admin/subscription/stats/overview", token=token)

    return {
        "users": user_stats,
        "enterprises": enterprise_stats,
        "payments": payment_stats,
        "trials": trial_stats,
        "subscriptions": subscription_stats,
        "catalog": {
            "brands": db.query(ForkliftBrand).count(),
            "series": db.query(ForkliftSeries).count(),
            "models": db.query(ForkliftModel).count(),
            "engine_brands": db.query(EngineBrand).count(),
            "engine_models": db.query(EngineModel).count(),
            "parts": db.query(Part).count(),
        },
        "assets": {
            "diagrams": db.query(Diagram).count(),
            "models3d": db.query(Model3D).count(),
        },
        "ai": {
            "knowledge_documents": db.query(KnowledgeDocument).count(),
            "fault_codes": db.query(FaultCode).count(),
            "fault_trees": db.query(FaultTree).count(),
        },
        "maintenance": {
            "forklifts": db.query(UserForklift).count(),
            "records": db.query(MaintenanceRecord).count(),
            "reminders": db.query(MaintenanceReminder).count(),
        },
    }