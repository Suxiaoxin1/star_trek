"""AI 智能分析路由 — 同步/异步分析、模型列表、任务状态、用量统计"""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import RoleChecker
from app.config import settings
from app.database import get_db
from app.models import MarketIntelligence, Competitor
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
    generate_streaming_report,
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
#  服务状态端点
# ================================================================

@router.get("/status")
async def get_ai_status(_user=require_analyst):
    """检查 AI 服务配置状态

    返回当前是否已配置可用的 LLM API Key 及模型信息。
    前端 AIAnalysis 页加载时调用，用于展示 AI 是否可用。
    """
    api_key = settings.OPENAI_API_KEY
    return {
        "available": bool(api_key),
        "model": settings.OPENAI_MODEL if api_key else None,
        "api_base": settings.OPENAI_API_BASE or "https://api.openai.com/v1",
        "message": "AI 服务已配置" if api_key else "未配置 OPENAI_API_KEY，请在 .env 中设置后重启服务",
    }


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


# 前端 AIReportGenerateParams 兼容：通过 competitor_id + intelligence_ids 拉取数据后生成
class ReportGenerateRequest(BaseModel):
    """前端 /ai/report/generate 请求体"""
    title: str | None = Field(None)
    competitor_id: str | None = Field(None)
    intelligence_ids: list[str] = Field(default_factory=list)
    intelligence_limit: int = Field(5, ge=1, le=50)
    report_type: str = Field("competitor_analysis")
    model: str | None = Field(None)
    tags: list[str] = Field(default_factory=list)


class StreamReportRequest(BaseModel):
    """前端 /ai/report/stream 请求体（同 ReportGenerateRequest）"""
    title: str | None = Field(None)
    competitor_id: str | None = Field(None)
    intelligence_ids: list[str] = Field(default_factory=list)
    intelligence_limit: int = Field(5, ge=1, le=50)
    report_type: str = Field("competitor_analysis")
    model: str | None = Field(None)
    tags: list[str] = Field(default_factory=list)


# 前端 /ai/competitor 请求体：通过 competitor_id 拉取数据后深度分析
class CompetitorByIdRequest(BaseModel):
    competitor_id: str = Field(...)
    intelligence_limit: int = Field(5, ge=1, le=50)
    model: str | None = Field(None)


@router.post("/sentiment")
async def post_sentiment(req: SentimentRequest, _user=require_analyst):
    """同步情感分析"""
    try:
        result = await analyze_sentiment_enhanced(req.text, model=req.model, provider=req.provider)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("Sentiment analysis error: {}", str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:500])


@router.post("/sentiment/intelligence/{intel_id}")
async def post_sentiment_intelligence(
    intel_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=require_analyst,
):
    """对指定情报执行情感分析，并将结果回写到数据库"""
    intel = await db.get(MarketIntelligence, intel_id)
    if not intel:
        raise HTTPException(status_code=404, detail="情报不存在")
    text = f"{intel.title} {intel.summary or ''}"
    if not text.strip():
        raise HTTPException(status_code=400, detail="情报内容为空，无法分析")
    result = await analyze_sentiment_enhanced(text)
    # 回写情感分析结果
    intel.sentiment = result.get("sentiment", intel.sentiment)
    await db.commit()
    return {**result, "intelligence_id": str(intel.id), "title": intel.title}


@router.post("/summary")
async def post_summary(req: SummaryRequest, _user=require_analyst):
    """同步摘要提取"""
    try:
        result = await extract_summary_enhanced(req.text, model=req.model, provider=req.provider)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error("Summary extraction error: {}", str(e)[:200])
        raise HTTPException(status_code=500, detail=str(e)[:500])


@router.post("/summary/intelligence/{intel_id}")
async def post_summary_intelligence(
    intel_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=require_analyst,
):
    """对指定情报提取摘要"""
    intel = await db.get(MarketIntelligence, intel_id)
    if not intel:
        raise HTTPException(status_code=404, detail="情报不存在")
    text = f"{intel.title} {intel.summary or ''}"
    if not text.strip():
        raise HTTPException(status_code=400, detail="情报内容为空，无法提取摘要")
    result = await extract_summary_enhanced(text)
    return {**result, "intelligence_id": str(intel.id), "title": intel.title}


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


async def _gather_intelligence(
    db: AsyncSession,
    competitor_id: str | None,
    intel_ids: list[str],
    limit: int,
) -> tuple[list[dict], dict | None]:
    """收集情报数据与竞品信息（供 /report/generate 与 /report/stream 复用）

    返回 (intelligence_data, competitor_info) 二元组。
    """
    intelligence_data: list[dict] = []
    competitor_info: dict | None = None

    # 拉取竞品信息
    if competitor_id:
        competitor = await db.get(Competitor, competitor_id)
        if competitor:
            competitor_info = {
                "id": str(competitor.id),
                "name": competitor.name,
                "description": competitor.description,
                "tier": competitor.tier,
                "tags": competitor.tags or [],
            }

    # 拉取情报
    if intel_ids:
        stmt = select(MarketIntelligence).where(MarketIntelligence.id.in_(intel_ids))
        rows = (await db.execute(stmt)).scalars().all()
        intelligence_data = [
            {
                "id": str(r.id),
                "title": r.title,
                "summary": r.summary,
                "category": r.category,
                "sentiment": r.sentiment,
                "importance": r.importance,
                "source_name": r.source_name,
                "published_at": r.published_at.isoformat() if r.published_at else None,
            }
            for r in rows
        ]
    elif competitor_id:
        # 按竞品拉取最近情报
        stmt = (
            select(MarketIntelligence)
            .where(MarketIntelligence.competitor_id == competitor_id)
            .order_by(MarketIntelligence.published_at.desc().nullslast())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
        intelligence_data = [
            {
                "id": str(r.id),
                "title": r.title,
                "summary": r.summary,
                "category": r.category,
                "sentiment": r.sentiment,
                "importance": r.importance,
                "source_name": r.source_name,
                "published_at": r.published_at.isoformat() if r.published_at else None,
            }
            for r in rows
        ]
    return intelligence_data, competitor_info


@router.post("/report/generate")
async def post_report_generate(
    req: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _user=require_analyst,
):
    """AI 生成分析报告（前端兼容接口）

    根据 competitor_id 和/或 intelligence_ids 自动拉取数据，调用 LLM 生成报告内容。
    """
    intelligence_data, competitor_info = await _gather_intelligence(
        db, req.competitor_id, req.intelligence_ids, req.intelligence_limit
    )
    if not intelligence_data and not competitor_info:
        raise HTTPException(status_code=400, detail="未提供可分析的情报或竞品数据")

    title = req.title or f"AI 生成报告 - {competitor_info.get('name', '未指定竞品') if competitor_info else '综合分析'}"
    content = await generate_report_enhanced(
        title=title,
        intelligence_data=intelligence_data,
        competitor_info=competitor_info,
        report_type=req.report_type,
        model=req.model,
    )
    # 同时保存到数据库 reports 表
    from app.models import AnalysisReport
    report = AnalysisReport(
        title=title,
        content=content,
        status="completed",
        report_type=req.report_type,
        tags=req.tags,
        generated_by="ai",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return {
        "id": str(report.id),
        "title": report.title,
        "content": report.content,
        "status": report.status,
        "report_type": report.report_type,
        "tags": report.tags,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.post("/report/stream")
async def post_report_stream(
    req: StreamReportRequest,
    _user=require_analyst,
):
    """AI 流式生成报告（SSE）

    返回 text/event-stream，前端通过 ReadableStream 逐块读取。
    注意：因 SSE 是长连接，无法使用 Depends(get_db)，需在生成器内手动创建会话。
    """
    from app.database import async_session

    async def event_generator():
        """SSE 事件生成器"""
        try:
            # 在生成器内手动获取数据库会话（SSE 长连接场景）
            async with async_session() as db:
                intelligence_data, competitor_info = await _gather_intelligence(
                    db, req.competitor_id, req.intelligence_ids, req.intelligence_limit
                )

            if not intelligence_data and not competitor_info:
                yield _sse_event("error", {"message": "未提供可分析的情报或竞品数据"})
                return

            title = req.title or f"AI 生成报告 - {competitor_info.get('name', '未指定竞品') if competitor_info else '综合分析'}"
            full_content = ""
            async for chunk in generate_streaming_report(
                title=title,
                intelligence_data=intelligence_data,
                competitor_info=competitor_info,
                report_type=req.report_type,
                model=req.model,
            ):
                full_content += chunk
                yield _sse_event("delta", {"content": chunk})

            # 流结束后保存到数据库
            async with async_session() as db:
                from app.models import AnalysisReport
                report = AnalysisReport(
                    title=title,
                    content=full_content,
                    status="completed",
                    report_type=req.report_type,
                    tags=req.tags,
                    generated_by="ai",
                )
                db.add(report)
                await db.commit()
                await db.refresh(report)
                yield _sse_event("done", {
                    "id": str(report.id),
                    "title": report.title,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                })
        except Exception as e:
            logger.error("Stream report error: {}", str(e)[:200])
            yield _sse_event("error", {"message": str(e)[:500]})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse_event(event: str, data: dict) -> str:
    """构造 SSE 事件字符串"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/competitor/analyze")
async def post_competitor_analyze(req: CompetitorAnalysisRequest, _user=require_analyst):
    """同步竞品深度分析（原始接口：传入完整数据）"""
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


@router.post("/competitor")
async def post_competitor_by_id(
    req: CompetitorByIdRequest,
    db: AsyncSession = Depends(get_db),
    _user=require_analyst,
):
    """竞品深度分析（前端兼容接口：传入 competitor_id，自动拉取数据）

    前端 aiApi.competitorAnalysis(competitorId) 调用此端点。
    """
    competitor = await db.get(Competitor, req.competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="竞品不存在")
    competitor_info = {
        "id": str(competitor.id),
        "name": competitor.name,
        "description": competitor.description,
        "tier": competitor.tier,
        "tags": competitor.tags or [],
    }
    # 拉取该竞品最近情报
    stmt = (
        select(MarketIntelligence)
        .where(MarketIntelligence.competitor_id == req.competitor_id)
        .order_by(MarketIntelligence.published_at.desc().nullslast())
        .limit(req.intelligence_limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    intelligence_data = [
        {
            "id": str(r.id),
            "title": r.title,
            "summary": r.summary,
            "category": r.category,
            "sentiment": r.sentiment,
            "importance": r.importance,
        }
        for r in rows
    ]
    from app.services.llm_enhanced import analyze_competitor
    result = await analyze_competitor(
        competitor_info,
        intelligence_data,
        model=req.model,
    )
    return result


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
async def batch_sentiment(
    req: BatchSentimentRequest,
    db: AsyncSession = Depends(get_db),
    _user=require_analyst,
):
    """批量对选中情报执行情感分析"""
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


class SentimentBatchCompatRequest(BaseModel):
    """前端 /sentiment/batch 兼容请求体

    支持两种形式：
      1) { texts: [...], model: "..." }       —— 前端直接传文本
      2) { intelligence_ids: [...], model: ""} —— 走情报 ID 流程
    """
    texts: list[str] | None = Field(None)
    intelligence_ids: list[str] | None = Field(None)
    model: str | None = Field(None)


@router.post("/sentiment/batch")
async def sentiment_batch_alias(
    req: SentimentBatchCompatRequest,
    db: AsyncSession = Depends(get_db),
    _user=require_analyst,
):
    """批量情感分析（前端兼容端点）

    前端 aiApi.sentimentBatch(texts) 传入文本数组，直接对每条文本做情感分析。
    若传入 intelligence_ids，则按情报 ID 流程处理。
    """
    # 1) 前端传 texts，直接分析（不涉及数据库）
    if req.texts:
        results = []
        for text in req.texts:
            if not text.strip():
                results.append({"sentiment": "unknown", "sentiment_score": 0.0, "confidence": 0.0})
                continue
            try:
                result = await analyze_sentiment_enhanced(text, model=req.model)
                results.append(result)
            except Exception as e:
                logger.error("Sentiment batch error: {}", str(e)[:200])
                results.append({
                    "sentiment": "unknown",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "error": str(e)[:200],
                })
        return results

    # 2) 传 intelligence_ids，走情报流程（复用 batch_sentiment 的逻辑）
    if req.intelligence_ids:
        intel_req = BatchSentimentRequest(intelligence_ids=req.intelligence_ids)
        return await batch_sentiment(intel_req, db=db, _user=_user)

    # 都没传，返回空列表
    return []