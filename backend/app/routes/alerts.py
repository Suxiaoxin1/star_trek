"""预警管理路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/rules")
async def list_alert_rules():
    """获取预警规则列表"""
    return {"items": [], "total": 0}


@router.get("/history")
async def list_alert_history():
    """获取预警历史"""
    return {"items": [], "total": 0}
