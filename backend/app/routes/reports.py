"""分析报告路由 — CRUD（含权限控制）"""
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RoleChecker
from app.database import get_db
from app.models import AnalysisReport, MarketIntelligence
from app.schemas import ReportCreate, ReportResponse

router = APIRouter()

require_viewer = Depends(RoleChecker("admin", "analyst", "viewer"))
require_editor = Depends(RoleChecker("admin", "analyst"))
require_admin = Depends(RoleChecker("admin"))


@router.get("/", response_model=dict)
async def list_reports(
    status: str | None = Query(None),
    report_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user=require_viewer,
):
    """获取报告列表"""
    conditions = []
    if status:
        conditions.append(AnalysisReport.status == status)
    if report_type:
        conditions.append(AnalysisReport.report_type == report_type)

    count_q = select(func.count(AnalysisReport.id))
    if conditions:
        count_q = count_q.where(*conditions)
    total = (await db.execute(count_q)).scalar()

    q = select(AnalysisReport).order_by(AnalysisReport.created_at.desc())
    if conditions:
        q = q.where(*conditions)
    q = q.offset((page - 1) * page_size).limit(page_size)

    rows = (await db.execute(q)).scalars().all()
    items = [ReportResponse.model_validate(r).model_dump() for r in rows]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{report_id}", response_model=dict)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=require_viewer,
):
    """获取报告详情"""
    q = select(AnalysisReport).where(AnalysisReport.id == report_id)
    result = (await db.execute(q)).scalars().first()
    if not result:
        raise HTTPException(status_code=404, detail="报告不存在")

    return ReportResponse.model_validate(result).model_dump()


@router.post("/", status_code=201, response_model=dict)
async def create_report(
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db),
    _user=require_editor,
):
    """创建分析报告"""
    if payload.intelligence_id:
        intel = (await db.execute(
            select(MarketIntelligence.id).where(
                MarketIntelligence.id == payload.intelligence_id
            )
        )).scalars().first()
        if not intel:
            raise HTTPException(status_code=404, detail="关联情报不存在")

    report = AnalysisReport(**payload.model_dump())
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return ReportResponse.model_validate(report).model_dump()


@router.put("/{report_id}", response_model=dict)
async def update_report(
    report_id: UUID,
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db),
    _user=require_editor,
):
    """更新报告"""
    report = (await db.execute(
        select(AnalysisReport).where(AnalysisReport.id == report_id)
    )).scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
    report.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(report)
    return ReportResponse.model_validate(report).model_dump()


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=require_admin,
):
    """删除报告 — 仅管理员"""
    report = (await db.execute(
        select(AnalysisReport).where(AnalysisReport.id == report_id)
    )).scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    await db.delete(report)
    await db.flush()
    return {"detail": "报告已删除"}