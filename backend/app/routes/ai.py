"""AI 智能分析路由 — 同步/异步分析、模型列表、任务状态、用量统计"""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import RoleChecker
from app.schemas_ai_extra import (
    ModelsListResponse,
    TaskStatusResponse,
    UsageStatsResponse,
)
from app.services import llm
from app.services.llm_enhanced import (
    analyze_sentiment as analyze_sentiment_enhanced,
    extract_summary as extract_summary_enhanced,
    generate_report as generate_report_enhanced,
    list_available_models,
    get_token_usage_summary,
)
from app.tasks.ai_analysis import (
    analyze_intelligence_batch,
    generate_report_async,
    deep_competitor_analysis,
)

logger = logging.getLogger(__name__)

router = APIRouter()

require_analyst = Depends(RoleChecker("admin", "analyst"))
require_admin = Depends(RoleChecker("admin"))


# ================================================================
#  同步分析端点（轻量、即时返回）
# ================================================================

class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, description="待分析文本")
    model: str | None = Field(None, description="可选模型 ID")
    provider: str | None = Field(None, description="可选提供商名称")


class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=1, description="待摘要文本")
    model: str | None = Field(None)
    provider: str | None = Field(None)


class ReportRequest(BaseModel):
    title: str = Field(..., min_length=1)
    intelligence_data: list[dict[str, Any]] = Field(default_factory=list)
    competitor_info: dict[str, Any] | None = Field(None)
    report_type: str = Field(default="competitor_analysis")
    model: str | None = Field(None)
    provider: str | None = Field(None)


class CompetitorAnalysisRequest(BaseModel):
    competitor_info: dict[str, Any] = Field(...)
    intelligence_data: list[dict[str, Any]] = Field(default_factory=list)
    model: str | None = Field(None)
    provider: str | None = Field(None)


@router.post("/sentiment")
async def post_sentiment(req: SentimentRequest, _user=require_analyst):
    """同步情感分析"""
    try:
        result = await analyze_sentiment_enhanced(req.text, model=req.model, provider=req.provider)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("Sentiment analysis error: {}", str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:500])


@router.post("/summary")
async def post_summary(req: SummaryRequest, _user=require_analyst):
    """同步摘要提取"""
    try:
        result = await extract_summary_enhanced(req.text, model=req.model, provider=req.provider)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("Summary extraction error: {}", str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:500])


@router.post("/report")
async def post_report(req: ReportRequest, _user=require_analyst):
    """同步生成分析报告"""
    try:
        content = await generate_report_enhanced(
            title=req.title,
            intelligence_data=req.intelligence_data,
            competitor_info=req.competitor_info,
            report_type=req.report_type,
            model=req.model,
            provider=req.provider,
        )
        return {"success": True, "content": content}
    except Exception as e:
        logger.error("Report generation error: {}", str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:500])


@router.post("/competitor/analyze")
async def post_competitor_analyze(req: CompetitorAnalysisRequest, _user=require_analyst):
    """同步竞品深度分析"""
    try:
        from app.services.llm_enhanced import analyze_competitor
        result = await analyze_competitor(
            req.competitor_info,
            req.intelligence_data,
            model=req.model,
            provider=req.provider,
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("Competitor analysis error: {}", str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:500])


# ================================================================
#  异步任务触发端点
# ================================================================

class BatchAnalyzeRequest(BaseModel):
    intelligence_ids: list[str] = Field(..., min_length=1)


class AsyncReportRequest(BaseModel):
    title: str = Field(..., min_length=1)
    intelligence_ids: list[str] = Field(default_factory=list)
    report_type: str = Field(default="daily_briefing")


class AsyncCompetitorRequest(BaseModel):
    competitor_id: str = Field(...)


@router.post("/task/batch-analyze")
async def trigger_batch_analyze(req: BatchAnalyzeRequest, _user=require_analyst):
    """触发批量情感分析 + 摘要任务"""
    task = analyze_intelligence_batch.delay(req.intelligence_ids)
    return {
        "success": True,
        "task_id": str(task.id),
        "status_url": f"/ai/task/{task.id}",
        "message": f"已提交 {len(req.intelligence_ids)} 条情报的批量分析任务",
    }


@router.post("/task/generate-report")
async def trigger_generate_report(req: AsyncReportRequest, _user=require_analyst):
    """触发异步报告生成"""
    task = generate_report_async.delay(req.title, req.intelligence_ids, req.report_type)
    return {
        "success": True,
        "task_id": str(task.id),
        "status_url": f"/ai/task/{task.id}",
        "message": "报告生成任务已提交",
    }


@router.post("/task/deep-competitor-analysis")
async def trigger_deep_competitor(req: AsyncCompetitorRequest, _user=require_analyst):
    """触发异步竞品深度分析"""
    task = deep_competitor_analysis.delay(req.competitor_id)
    return {
        "success": True,
        "task_id": str(task.id),
        "status_url": f"/ai/task/{task.id}",
        "message": "竞品深度分析任务已提交",
    }


# ================================================================
#  模型列表端点
# ================================================================

@router.get("/models", response_model=ModelsListResponse)
async def list_models(_user=require_admin):
    """列出所有可用 LLM 模型"""
    models = list_available_models()
    return ModelsListResponse(models=models, total=len(models))


# ================================================================
#  任务状态查询端点
# ================================================================

_task_cache: dict[str, dict[str, Any]] = {}


def _record_task_status(task_id: str, status: str, progress: int = 0,
                        current_step: str = "", result: dict | None = None,
                        error: str | None = None) -> None:
    """记录任务状态到缓存"""
    _task_cache[task_id] = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "current_step": current_step,
        "total_steps": 1,
        "result": result,
        "error": error,
    }


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, _user=require_analyst):
    """查询异步任务进度"""
    cached = _task_cache.get(task_id)
    if cached:
        return TaskStatusResponse(success=True, task=cached)

    try:
        from app.tasks.celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        status_info = {
            "task_id": task_id,
            "status": result.status,
            "progress": 0,
            "current_step": "",
            "total_steps": 0,
            "result": None,
            "error": str(result.result) if result.failed() else None,
        }
        if result.ready():
            status_info["progress"] = 100
            status_info["result"] = result.result if not result.failed() else None
        return TaskStatusResponse(success=True, task=status_info)
    except Exception:
        pass

    return TaskStatusResponse(success=False, task=None)


# ================================================================
#  用量统计端点
# ================================================================

@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    period: str = Query("day", description="统计周期: day/week/month"),
    provider: str | None = Query(None, description="按提供商过滤"),
    _user=require_admin,
):
    """获取 Token 用量统计"""
    stats = get_token_usage_summary(period=period, provider=provider)
    return UsageStatsResponse(success=True, stats=stats)


# ================================================================
#  批量情感分析（前端一键操作）
# ================================================================

class BatchSentimentRequest(BaseModel):
    intelligence_ids: list[str] = Field(..., min_length=1)


@router.post("/batch/sentiment")
async def batch_sentiment(req: BatchSentimentRequest, _user=require_analyst):
    """批量对选中情报执行情感分析"""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database import get_db
    from app.models import MarketIntelligence

    async for db in get_db():
        try:
            results = []
            for intel_id in req.intelligence_ids:
                stmt = select(MarketIntelligence).where(MarketIntelligence.id == intel_id)
                row = await db.execute(stmt)
                intel = row.scalar_one_or_none()
                if not intel:
                    results.append({"id": intel_id, "status": "not_found"})
                    continue

                text = f"{intel.title} {intel.summary or ''}"
                if not text.strip():
                    results.append({"id": intel_id, "status": "empty_text"})
                    continue

                try:
                    sentiment_result = await llm.analyze_sentiment(text)
                    intel.sentiment = sentiment_result.get("sentiment", intel.sentiment)
                    await db.commit()
                    results.append({"id": intel_id, "status": "ok", "result": sentiment_result})
                except Exception as e:
                    await db.rollback()
                    results.append({"id": intel_id, "status": "error", "error": str(e)[:200]})

            return {"success": True, "results": results}
        finally:
            await db.close()
            break

    raise HTTPException(status_code=500, detail="Database connection failed")