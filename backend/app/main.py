from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.core.database import engine, Base
from app.api.auth import router as auth_router
from app.api.forklift import router as forklift_router, engine_router
from app.api.parts import router as parts_router, diagram_router
from app.api.maintenance import router as maintenance_router
from app.api.ai import router as ai_router
from app.api.embed import router as embed_router
from app.api.model3d import router as model3d_router, ar_router
from app.api.admin import router as admin_router
from app.api.knowledge import router as knowledge_router
from app.api.manual import router as manual_router
from app.api.proxy import routers as account_proxy_routers
from app.core.error_handler import register_exception_handlers
from app.core import dependencies_check

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ForkliftCLI — 智能叉车维修辅助系统 API",
)

# 本地存储模式：将 uploads 目录挂载为静态资源访问入口。
if settings.STORAGE_PROVIDER.lower() == "local":
    import os

    uploads_dir = os.path.abspath(settings.UPLOAD_DIR)
    if os.path.isdir(uploads_dir):
        app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(forklift_router, prefix="/api/v1")
app.include_router(engine_router, prefix="/api/v1")
app.include_router(parts_router, prefix="/api/v1")
app.include_router(diagram_router, prefix="/api/v1")
app.include_router(maintenance_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(embed_router, prefix="/api/v1")
app.include_router(model3d_router, prefix="/api/v1")
app.include_router(ar_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(manual_router, prefix="/api/v1")
for router in account_proxy_routers:
    app.include_router(router, prefix="/api/v1")

# 全局异常处理
register_exception_handlers(app)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    dependencies_check.log_dependency_states()


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    # status 保持恒为 ok：探活端点只表示进程活着，依赖状态放在 dependencies 里
    # 单独暴露，编排层要降级就自己判这个字段，避免误把探活当业务健康。
    return {"status": "ok", "dependencies": dependencies_check.dependency_states()}
