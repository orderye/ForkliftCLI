"""后台管理 API 路由聚合（/api/v1/admin/*）"""
from fastapi import APIRouter

from app.api.admin.assets import router as assets_router
from app.api.admin.audit import router as audit_router
from app.api.admin.catalog import router as catalog_router
from app.api.admin.compliance import router as compliance_router
from app.api.admin.dashboard import router as dashboard_router
from app.api.admin.enterprises import router as enterprises_router
from app.api.admin.knowledge import router as knowledge_router
from app.api.admin.users import router as users_router

router = APIRouter()
router.include_router(users_router)
router.include_router(enterprises_router)
router.include_router(catalog_router)
router.include_router(assets_router)
router.include_router(knowledge_router)
router.include_router(compliance_router)
router.include_router(dashboard_router)
router.include_router(audit_router)
