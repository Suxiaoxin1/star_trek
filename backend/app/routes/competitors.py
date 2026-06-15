"""竞品管理路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/")
async def list_competitors(
    tier: str | None = Query(None, description="竞品层级: direct/indirect/potential"),
    is_active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """获取竞品列表"""
    return {"items": [], "total": 0}


@router.get("/{competitor_id}")
async def get_competitor(competitor_id: str):
    """获取竞品详情"""
    return {"id": competitor_id}


@router.get("/{competitor_id}/products")
async def get_competitor_products(competitor_id: str):
    """获取竞品产品列表"""
    return {"items": []}


@router.get("/{competitor_id}/features")
async def get_competitor_features(competitor_id: str):
    """获取竞品功能对比"""
    return {"items": []}


@router.get("/{competitor_id}/pricing-history")
async def get_pricing_history(competitor_id: str):
    """获取价格变动历史"""
    return {"items": []}
