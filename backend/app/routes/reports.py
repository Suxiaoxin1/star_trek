"""分析报告路由"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_reports():
    """获取报告列表"""
    return {"items": [], "total": 0}


@router.get("/{report_id}")
async def get_report(report_id: str):
    """获取报告详情"""
    return {"id": report_id}
