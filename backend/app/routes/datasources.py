"""数据源管理 & 采集数据查看 API（含权限控制）"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RoleChecker
from app.database import get_db as get_session
from app.models import DataSource, CollectedData
from app.schemas import (
    DataSourceCreate, DataSourceUpdate, DataSourceResponse,
    CollectedDataResponse, PaginatedResponse,
)
from app.tasks.crawler import crawl_single_source, crawl_all_sources, crawl_sources_by_type

router = APIRouter()

require_viewer = Depends(RoleChecker("admin", "analyst", "viewer"))
require_editor = Depends(RoleChecker("admin", "analyst"))
require_admin = Depends(RoleChecker("admin"))


# ======================= 固定路径（必须在动态路径之前） =======================

@router.get("/stats")
async def datasource_stats(
    session: AsyncSession = Depends(get_session),
    _user=require_viewer,
):
    """数据源统计"""
    total = (await session.execute(select(func.count()).select_from(DataSource))).scalar() or 0
    active = (await session.execute(select(func.count()).select_from(DataSource).filter(DataSource.is_active == True))).scalar() or 0
    by_type = {}
    type_rows = (await session.execute(
        select(DataSource.source_type, func.count()).group_by(DataSource.source_type)
    )).all()
    for t, c in type_rows:
        by_type[t] = c

    by_status = {}
    status_rows = (await session.execute(
        select(DataSource.last_status, func.count()).filter(DataSource.last_status.isnot(None)).group_by(DataSource.last_status)
    )).all()
    for s, c in status_rows:
        by_status[s] = c

    return {
        "total": total,
        "active": active,
        "inactive": total - active,
        "by_type": by_type,
        "by_status": by_status,
    }


@router.post("/crawl-all")
async def trigger_crawl_all(
    _user=require_editor,
):
    """手动触发所有数据源采集 — 分析师和管理员"""
    task = crawl_all_sources.delay()
    return {"task_id": task.id, "status": "dispatched"}


@router.post("/crawl-by-type/{source_type}")
async def trigger_crawl_by_type(
    source_type: str,
    _user=require_editor,
):
    """按类型触发采集 — 分析师和管理员"""
    valid_types = ["rss", "api", "web_scraper", "social_media", "news"]
    if source_type not in valid_types:
        raise HTTPException(400, f"不支持的数据源类型: {source_type}")
    task = crawl_sources_by_type.delay(source_type)
    return {"task_id": task.id, "source_type": source_type, "status": "dispatched"}


# ======================= 数据源 CRUD =======================

@router.get("/", response_model=PaginatedResponse)
async def list_datasources(
    source_type: str | None = None,
    is_active: bool | None = None,
    keyword: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _user=require_viewer,
):
    """数据源列表（支持筛选）"""
    query = select(DataSource)

    if source_type:
        query = query.filter(DataSource.source_type == source_type)
    if is_active is not None:
        query = query.filter(DataSource.is_active == is_active)
    if keyword:
        query = query.filter(DataSource.name.ilike(f"%{keyword}%"))

    total_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(total_q)).scalar() or 0

    query = query.order_by(DataSource.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[DataSourceResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=DataSourceResponse, status_code=201)
async def create_datasource(
    data: DataSourceCreate,
    session: AsyncSession = Depends(get_session),
    _user=require_editor,
):
    """创建数据源 — 分析师和管理员"""
    source = DataSource(**data.model_dump())
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return DataSourceResponse.model_validate(source)


@router.get("/{source_id}", response_model=DataSourceResponse)
async def get_datasource(
    source_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=require_viewer,
):
    """获取单个数据源详情"""
    source = await session.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "数据源不存在")
    return DataSourceResponse.model_validate(source)


@router.put("/{source_id}", response_model=DataSourceResponse)
async def update_datasource(
    source_id: UUID,
    data: DataSourceUpdate,
    session: AsyncSession = Depends(get_session),
    _user=require_editor,
):
    """更新数据源 — 分析师和管理员"""
    source = await session.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "数据源不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)

    await session.commit()
    await session.refresh(source)
    return DataSourceResponse.model_validate(source)


@router.delete("/{source_id}")
async def delete_datasource(
    source_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=require_admin,
):
    """删除数据源 — 仅管理员"""
    source = await session.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "数据源不存在")
    await session.delete(source)
    await session.commit()
    return {"message": "已删除"}


@router.post("/{source_id}/crawl")
async def trigger_crawl(
    source_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=require_editor,
):
    """手动触发单个数据源采集 — 分析师和管理员"""
    source = await session.get(DataSource, source_id)
    if not source:
        raise HTTPException(404, "数据源不存在")
    if not source.is_active:
        raise HTTPException(400, "数据源已禁用，无法采集")

    task = crawl_single_source.delay(str(source_id))
    return {"task_id": task.id, "source_id": str(source_id), "status": "dispatched"}


# ======================= 采集数据查看 =======================
collected_router = APIRouter()


@collected_router.get("/stats")
async def collected_data_stats(
    session: AsyncSession = Depends(get_session),
    _user=require_viewer,
):
    """采集数据统计"""
    total = (await session.execute(select(func.count()).select_from(CollectedData))).scalar() or 0
    processed = (await session.execute(select(func.count()).select_from(CollectedData).filter(CollectedData.processed == True))).scalar() or 0
    unprocessed = total - processed

    by_source = {}
    source_rows = (await session.execute(
        select(CollectedData.source_id, func.count()).group_by(CollectedData.source_id)
    )).all()
    for sid, c in source_rows:
        if sid:
            source = await session.get(DataSource, sid)
            name = source.name if source else str(sid)
            by_source[name] = c

    by_language = {}
    lang_rows = (await session.execute(
        select(CollectedData.language, func.count()).group_by(CollectedData.language)
    )).all()
    for l, c in lang_rows:
        by_language[l] = c

    latest = (await session.execute(
        select(func.max(CollectedData.collected_at))
    )).scalar()

    return {
        "total": total,
        "processed": processed,
        "unprocessed": unprocessed,
        "by_source": by_source,
        "by_language": by_language,
        "latest_collected_at": latest.isoformat() if latest else None,
    }


@collected_router.get("/", response_model=PaginatedResponse)
async def list_collected_data(
    source_id: UUID | None = None,
    processed: bool | None = None,
    keyword: str | None = None,
    language: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _user=require_viewer,
):
    """采集数据列表"""
    query = select(CollectedData)

    if source_id:
        query = query.filter(CollectedData.source_id == source_id)
    if processed is not None:
        query = query.filter(CollectedData.processed == processed)
    if language:
        query = query.filter(CollectedData.language == language)
    if keyword:
        query = query.filter(CollectedData.title.ilike(f"%{keyword}%"))

    total_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(total_q)).scalar() or 0

    query = query.order_by(CollectedData.collected_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    items = result.scalars().all()

    response_items = []
    for item in items:
        resp = CollectedDataResponse.model_validate(item)
        if item.source_id:
            source = await session.get(DataSource, item.source_id)
            resp.source_name = source.name if source else ""
        response_items.append(resp)

    return PaginatedResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
    )


@collected_router.get("/{data_id}", response_model=CollectedDataResponse)
async def get_collected_data(
    data_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=require_viewer,
):
    """获取单条采集数据"""
    item = await session.get(CollectedData, data_id)
    if not item:
        raise HTTPException(404, "采集数据不存在")

    resp = CollectedDataResponse.model_validate(item)
    if item.source_id:
        source = await session.get(DataSource, item.source_id)
        resp.source_name = source.name if source else ""
    return resp


@collected_router.put("/{data_id}/process")
async def mark_processed(
    data_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=require_editor,
):
    """标记为已处理 — 分析师和管理员"""
    item = await session.get(CollectedData, data_id)
    if not item:
        raise HTTPException(404, "采集数据不存在")
    item.processed = True
    await session.commit()
    return {"message": "已标记为已处理"}


@collected_router.delete("/{data_id}")
async def delete_collected_data(
    data_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=require_admin,
):
    """删除采集数据 — 仅管理员"""
    item = await session.get(CollectedData, data_id)
    if not item:
        raise HTTPException(404, "采集数据不存在")
    await session.delete(item)
    await session.commit()
    return {"message": "已删除"}