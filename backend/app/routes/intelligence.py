"""市场情报路由 — CRUD"""
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Competitor, MarketIntelligence
from app.schemas import IntelligenceCreate, IntelligenceResponse

router = APIRouter()


@router.get("/", response_model=dict)
async def list_intelligence(
    competitor_id: UUID | None = Query(None),
    category: str | None = Query(None),
    sentiment: str | None = Query(None),
    importance: int | None = Query(None, ge=1, le=5),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取情报列表（分页 + 多维度筛选）"""
    conditions = []
    if competitor_id:
        conditions.append(MarketIntelligence.competitor_id == competitor_id)
    if category:
        conditions.append(MarketIntelligence.category == category)
    if sentiment:
        conditions.append(MarketIntelligence.sentiment == sentiment)
    if importance:
        conditions.append(MarketIntelligence.importance >= importance)
    if keyword:
        conditions.append(
            MarketIntelligence.title.ilike(f"%{keyword}%") |
            (MarketIntelligence.summary.ilike(f"%{keyword}%") if hasattr(MarketIntelligence.summary, 'ilike') else True)
        )

    # 总数
    count_q = select(func.count(MarketIntelligence.id))
    if conditions:
        count_q = count_q.where(*conditions)
    total = (await db.execute(count_q)).scalar()

    # 列表（按发布时间倒序）
    q = (
        select(MarketIntelligence)
        .order_by(MarketIntelligence.published_at.desc().nullslast())
    )
    if conditions:
        q = q.where(*conditions)
    q = q.offset((page - 1) * page_size).limit(page_size)

    rows = (await db.execute(q)).scalars().all()

    # 批量获取竞品名称
    comp_ids = {r.competitor_id for r in rows}
    name_map = {}
    if comp_ids:
        comp_q = select(Competitor.id, Competitor.name).where(Competitor.id.in_(comp_ids))
        name_map = {c.id: c.name for c in (await db.execute(comp_q)).all()}

    items = []
    for r in rows:
        d = IntelligenceResponse.model_validate(r).model_dump()
        d["competitor_name"] = name_map.get(r.competitor_id, "")
        items.append(d)

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/stats", response_model=dict)
async def intelligence_stats(db: AsyncSession = Depends(get_db)):
    """情报统计概览"""
    # 按分类统计
    cat_q = (
        select(MarketIntelligence.category, func.count())
        .group_by(MarketIntelligence.category)
    )
    by_category = {row[0]: row[1] for row in (await db.execute(cat_q)).all()}

    # 按情感统计
    sent_q = (
        select(MarketIntelligence.sentiment, func.count())
        .group_by(MarketIntelligence.sentiment)
    )
    by_sentiment = {row[0]: row[1] for row in (await db.execute(sent_q)).all()}

    # 总数
    total = (await db.execute(select(func.count(MarketIntelligence.id)))).scalar()

    return {
        "total": total,
        "by_category": by_category,
        "by_sentiment": by_sentiment,
    }


@router.get("/{intel_id}", response_model=dict)
async def get_intelligence(intel_id: UUID, db: AsyncSession = Depends(get_db)):
    """获取情报详情"""
    q = select(MarketIntelligence).where(MarketIntelligence.id == intel_id)
    result = (await db.execute(q)).scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="情报不存在")

    d = IntelligenceResponse.model_validate(result).model_dump()
    # 补充竞品名
    comp = (await db.execute(
        select(Competitor.name).where(Competitor.id == result.competitor_id)
    )).scalars().first()
    d["competitor_name"] = comp
    return d


@router.post("/", status_code=201, response_model=dict)
async def create_intelligence(
    payload: IntelligenceCreate,
    db: AsyncSession = Depends(get_db),
):
    """新增市场情报"""
    comp = (await db.execute(
        select(Competitor.id).where(Competitor.id == payload.competitor_id)
    )).scalars().first()
    if not comp:
        raise HTTPException(status_code=404, detail="竞品不存在")

    intel = MarketIntelligence(
        **payload.model_dump(),
        published_at=payload.published_at or datetime.utcnow(),
    )
    db.add(intel)
    await db.flush()
    await db.refresh(intel)
    d = IntelligenceResponse.model_validate(intel).model_dump()
    d["competitor_name"] = ""
    return d


@router.put("/{intel_id}", response_model=dict)
async def update_intelligence(
    intel_id: UUID,
    payload: IntelligenceCreate,
    db: AsyncSession = Depends(get_db),
):
    """更新情报"""
    intel = (await db.execute(
        select(MarketIntelligence).where(MarketIntelligence.id == intel_id)
    )).scalars().first()
    if not intel:
        raise HTTPException(status_code=404, detail="情报不存在")

    update_data = payload.model_dump(exclude={"competitor_id"})
    for field, value in update_data.items():
        setattr(intel, field, value)
    intel.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(intel)
    return IntelligenceResponse.model_validate(intel).model_dump()
