`\"路由聚合"""
from fastapi import APIRouter

from app.routes import competitors, intelligence, reports, alerts, auth, datasources, ai, llm_selection, llm_config

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(competitors.router, prefix="/competitors", tags=["竞品管理"])
router.include_router(intelligence.router, prefix="/intelligence", tags=["市场情报"])
router.include_router(reports.router, prefix="/reports", tags=["分析报告"])
router.include_router(alerts.router, prefix="/alerts", tags=["预警管理"])
router.include_router(datasources.router, prefix="/datasources", tags=["数据源管理"])
router.include_router(datasources.collected_router, prefix="/collected-data", tags=["采集数据"])
router.include_router(ai.router, prefix="/ai", tags=["AI 智能分析"])
router.include_router(llm_selection.router, prefix="/llm-selection", tags=["大模型选型"])
router.include_router(llm_config.router, prefix="/llm-config", tags=["LLM 模型配置"])
