"""路由聚合"""
from fastapi import APIRouter

from app.routes import competitors, intelligence, reports, alerts

router = APIRouter()

router.include_router(competitors.router, prefix="/competitors", tags=["竞品管理"])
router.include_router(intelligence.router, prefix="/intelligence", tags=["市场情报"])
router.include_router(reports.router, prefix="/reports", tags=["分析报告"])
router.include_router(alerts.router, prefix="/alerts", tags=["预警管理"])
