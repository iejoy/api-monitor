"""
API路由配置
"""
from fastapi import APIRouter
from .endpoints import services, monitor_logs, alert_configs, dashboard, settings, maintenance

# 创建主路由
api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(
    services.router,
    prefix="/services",
    tags=["services"]
)

api_router.include_router(
    monitor_logs.router,
    prefix="/logs",
    tags=["monitor_logs"]
)

api_router.include_router(
    alert_configs.router,
    prefix="/alerts",
    tags=["alert_configs"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"]
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"]
)

api_router.include_router(
    maintenance.router,
    prefix="/maintenance",
    tags=["maintenance"]
)