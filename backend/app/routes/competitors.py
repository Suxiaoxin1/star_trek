"""竞品管理路由 — 完整 CRUD"""
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Competitor, Product, CompetitorFeature, PricingHistory
from app.schemas import (
    CompetitorCreate, CompetitorUpdate, CompetitorResponse,
    ProductCreate, ProductResponse,
    FeatureCreate, FeatureResponse,
    PricingHistoryCreate, PricingHistoryResponse,
)

router = APIRouter()


# ================================================================
#  竞品 CRUD
# ================================================================

@router.get("/", response_model=dict)
async def list_competitors(
    tier: str | None = Query(None, description="竞品层级: direct/indirect/potential"),
    is_active: bool | None = Query(None),
    keyword: str | None = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取竞品列表（分页 + 筛选）"""
    conditions = []
    if tier:
        conditions.append(Competitor.tier == tier)
    if is_active is not None:
        conditions.append(Competitor.is_active == is_active)
    if keyword:
        conditions.append(Competitor.name.ilike(f"%{keyword}%"))

    # 查询总数
    count_q = select(func.count(Competitor.id))
    if conditions:
        count_q = count_q.where(*conditions)
    total = (await db.execute(count_q)).scalar()

    # 查询列表
    q = select(Competitor).order_by(Competitor.created_at.desc())
    if conditions:
        q = q.where(*conditions)
    q = q.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()

    items = []
    for c in rows:
        items.append(CompetitorResponse.model_validate(c).model_dump())

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{competitor_id}", response_model=dict)
async def get_competitor(competitor_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取竞品详情（含关联统计）"""
    q = (
        select(Competitor)
        .options(
            selectinload(Competitor.products),
            selectinload(Competitor.features),
        )
        .where(Competitor.id == competitor_id)
    )
    result = (await db.execute(q)).scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="竞品不存在")

    data = CompetitorResponse.model_validate(result).model_dump()
    data["products"] = [
        ProductResponse.model_validate(p).model_dump() for p in result.products
    ]
    data["features"] = [
        FeatureResponse.model_validate(f).model_dump() for f in result.features
    ]
    return data


@router.post("/", response_model=dict, status_code=201)
async def create_competitor(
    payload: CompetitorCreate,
    db: AsyncSession = Depends(get_db),
):
    """新增竞品"""
    comp = Competitor(**payload.model_dump())
    db.add(comp)
    await db.flush()
    await db.refresh(comp)
    return CompetitorResponse.model_validate(comp).model_dump()


@router.put("/{competitor_id}", response_model=dict)
async def update_competitor(
    competitor_id: UUID,
    payload: CompetitorUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新竞品信息"""
    q = select(Competitor).where(Competitor.id == competitor_id)
    comp = (await db.execute(q)).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comp, field, value)
    comp.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(comp)
    return CompetitorResponse.model_validate(comp).model_dump()


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: UUID,
    soft: bool = Query(True, description="软删除（仅标记为不活跃）"),
    db: AsyncSession = Depends(get_db),
):
    """删除竞品（默认软删除）"""
    q = select(Competitor).where(Competitor.id == competitor_id)
    comp = (await db.execute(q)).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    if soft:
        comp.is_active = False
        comp.updated_at = datetime.utcnow()
        await db.flush()
        return {"detail": "竞品已停用（软删除）"}
    else:
        await db.delete(comp)
        await db.flush()
        return {"detail": "竞品已永久删除"}


# ================================================================
#  竞品 → 产品
# ================================================================

@router.get("/{competitor_id}/products", response_model=dict)
async def list_products(
    competitor_id: UUID,
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取竞品的产品列表"""
    # 先确认竞品存在
    comp = (await db.execute(
        select(Competitor.id).where(Competitor.id == competitor_id)
    )).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    q = select(Product).where(Product.competitor_id == competitor_id)
    if is_active is not None:
        q = q.where(Product.is_active == is_active)
    q = q.order_by(Product.created_at.desc())

    rows = (await db.execute(q)).scalars().all()
    items = [ProductResponse.model_validate(p).model_dump() for p in rows]
    return {"items": items, "total": len(items)}


@router.post("/{competitor_id}/products", status_code=201, response_model=dict)
async def create_product(
    competitor_id: UUID,
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """为竞品新增产品"""
    comp = (await db.execute(
        select(Competitor.id).where(Competitor.id == competitor_id)
    )).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    product = Product(competitor_id=competitor_id, **payload.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return ProductResponse.model_validate(product).model_dump()


# ================================================================
#  竞品 → 功能对比
# ================================================================

@router.get("/{competitor_id}/features", response_model=dict)
async def list_features(
    competitor_id: UUID,
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取竞品功能列表（按分类筛选）"""
    comp = (await db.execute(
        select(Competitor.id).where(Competitor.id == competitor_id)
    )).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    q = select(CompetitorFeature).where(
        CompetitorFeature.competitor_id == competitor_id
    )
    if category:
        q = q.where(CompetitorFeature.category == category)
    q = q.order_by(CompetitorFeature.category, CompetitorFeature.feature_name)

    rows = (await db.execute(q)).scalars().all()
    items = [FeatureResponse.model_validate(f).model_dump() for f in rows]

    # 按分类聚合
    by_category: dict[str, list] = {}
    for item in items:
        cat = item["category"]
        by_category.setdefault(cat, []).append(item)

    return {"items": items, "total": len(items), "categories": by_category}


@router.post("/{competitor_id}/features", status_code=201, response_model=dict)
async def upsert_feature(
    competitor_id: UUID,
    payload: FeatureCreate,
    db: AsyncSession = Depends(get_db),
):
    """新增或更新功能点（Upsert）"""
    comp = (await db.execute(
        select(Competitor.id).where(Competitor.id == competitor_id)
    )).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    # 查找是否已存在同名功能
    q = select(CompetitorFeature).where(
        CompetitorFeature.competitor_id == competitor_id,
        CompetitorFeature.feature_name == payload.feature_name,
    )
    existing = (await db.execute(q)).scalars().first()

    if existing:
        # 更新
        update_data = payload.model_dump()
        for field, value in update_data.items():
            setattr(existing, field, value)
        existing.updated_at = datetime.utcnow()
        existing.verified_at = datetime.utcnow()
        await db.flush()
        await db.refresh(existing)
        return FeatureResponse.model_validate(existing).model_dump()
    else:
        # 新增
        feature = CompetitorFeature(
            competitor_id=competitor_id,
            **payload.model_dump(),
            verified_at=datetime.utcnow(),
        )
        db.add(feature)
        await db.flush()
        await db.refresh(feature)
        return FeatureResponse.model_validate(feature).model_dump()


# ================================================================
#  竞品 → 价格变动历史
# ================================================================

@router.get("/{competitor_id}/pricing-history", response_model=dict)
async def list_pricing_history(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取竞品价格变动历史"""
    comp = (await db.execute(
        select(Competitor.id).where(Competitor.id == competitor_id)
    )).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    q = (
        select(PricingHistory)
        .where(PricingHistory.competitor_id == competitor_id)
        .order_by(PricingHistory.detected_at.desc())
    )
    rows = (await db.execute(q)).scalars().all()
    items = [PricingHistoryResponse.model_validate(p).model_dump() for p in rows]
    return {"items": items, "total": len(items)}


@router.post("/{competitor_id}/pricing-history", status_code=201, response_model=dict)
async def record_pricing_change(
    competitor_id: UUID,
    payload: PricingHistoryCreate,
    db: AsyncSession = Depends(get_db),
):
    """记录价格变动"""
    comp = (await db.execute(
        select(Competitor.id).where(Competitor.id == competitor_id)
    )).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    record = PricingHistory(competitor_id=competitor_id, **payload.model_dump())
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return PricingHistoryResponse.model_validate(record).model_dump()
