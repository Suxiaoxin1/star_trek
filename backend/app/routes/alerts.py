"""预警管理路由 — CRUD"""
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import AlertRule, AlertHistory
from app.schemas import AlertRuleCreate, AlertRuleResponse, AlertHistoryResponse

router = APIRouter()


# ==================== 预警规则 ====================

@router.get("/rules", response_model=dict)
async def list_alert_rules(
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取预警规则列表"""
    q = select(AlertRule).order_by(AlertRule.created_at.desc())
    if is_active is not None:
        q = q.where(AlertRule.is_active == is_active)

    rows = (await db.execute(q)).scalars().all()
    items = [AlertRuleResponse.model_validate(r).model_dump() for r in rows]
    return {"items": items, "total": len(items)}


@router.post("/rules", status_code=201, response_model=dict)
async def create_alert_rule(
    payload: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建预警规则"""
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return AlertRuleResponse.model_validate(rule).model_dump()


@router.put("/rules/{rule_id}", response_model=dict)
async def update_alert_rule(
    rule_id: UUID,
    payload: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """更新预警规则"""
    rule = (await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )).scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    rule.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(rule)
    return AlertRuleResponse.model_validate(rule).model_dump()


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: UUID, db: AsyncSession = Depends(get_db)):
    """删除预警规则"""
    rule = (await db.execute(
        select(AlertRule).where(AlertRule.id == rule_id)
    )).scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    await db.delete(rule)
    await db.flush()
    return {"detail": "规则已删除"}


# ==================== 预警历史 ====================

@router.get("/history", response_model=dict)
async def list_alert_history(
    rule_id: UUID | None = Query(None),
    is_read: bool | None = Query(None),
    severity: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取预警历史"""
    conditions = []
    if rule_id:
        conditions.append(AlertHistory.rule_id == rule_id)
    if is_read is not None:
        conditions.append(AlertHistory.is_read == is_read)
    if severity:
        conditions.append(AlertHistory.severity == severity)

    count_q = select(func.count(AlertHistory.id))
    if conditions:
        count_q = count_q.where(*conditions)
    total = (await db.execute(count_q)).scalar()

    q = (
        select(AlertHistory)
        .order_by(AlertHistory.triggered_at.desc())
        .options(selectinload(AlertHistory.rule))
    )
    if conditions:
        q = q.where(*conditions)
    q = q.offset((page - 1) * page_size).limit(page_size)

    rows = (await db.execute(q)).scalars().all()
    items = []
    for r in rows:
        d = AlertHistoryResponse.model_validate(r).model_dump()
        d["rule_name"] = r.rule.name if r.rule else ""
        items.append(d)

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/history/{alert_id}/read")
async def mark_alert_read(alert_id: UUID, db: AsyncSession = Depends(get_db)):
    """标记预警为已读"""
    alert = (await db.execute(
        select(AlertHistory).where(AlertHistory.id == alert_id)
    )).scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    alert.is_read = True
    await db.flush()
    return {"detail": "已标记为已读"}


@router.put("/history/{alert_id}/resolve")
async def resolve_alert(alert_id: UUID, db: AsyncSession = Depends(get_db)):
    """标记预警为已处理"""
    alert = (await db.execute(
        select(AlertHistory).where(AlertHistory.id == alert_id)
    )).scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    alert.is_resolved = True
    await db.flush()
    return {"detail": "预警已处理"}


@router.get("/stats", response_model=dict)
async def alert_stats(db: AsyncSession = Depends(get_db)):
    """预警统计"""
    unread = (await db.execute(
        select(func.count(AlertHistory.id)).where(AlertHistory.is_read == False)
    )).scalar()
    unresolved = (await db.execute(
        select(func.count(AlertHistory.id)).where(AlertHistory.is_resolved == False)
    )).scalar()
    active_rules = (await db.execute(
        select(func.count(AlertRule.id)).where(AlertRule.is_active == True)
    )).scalar()

    return {
        "unread_alerts": unread,
        "unresolved_alerts": unresolved,
        "active_rules": active_rules,
    }
