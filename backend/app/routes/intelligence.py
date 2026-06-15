"""市场情报路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/")
async def list_intelligence(
    competitor_id: str | None = Query(None),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取情报列表"""
    return {"items": [], "total": 0}


@router.get("/{intel_id}")
async def get_intelligence(intel_id: str):
    """获取情报详情"""
    return {"id": intel_id}
