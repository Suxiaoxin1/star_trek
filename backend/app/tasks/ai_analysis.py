"""AI 分析任务 — 实现日报/周报生成和预警检查"""
import json
import logging
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import MarketIntelligence, AnalysisReport, AlertRule, AlertHistory, Competitor
from app.services.llm import generate_report, analyze_sentiment, extract_summary
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Celery worker 使用同步数据库引擎
sync_engine = create_engine(settings.DATABASE_URL_SYNC, pool_size=5, max_overflow=10)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def analyze_intelligence(self, intel_id: str):
    """AI 分析单条情报：情感分析 + 摘要提取"""
    session = SyncSession()
    try:
        intel = session.query(MarketIntelligence).filter(MarketIntelligence.id == intel_id).first()
        if not intel:
            logger.warning(f"情报不存在: {intel_id}")
            return {"intel_id": intel_id, "status": "not_found"}

        # 构建分析文本
        text = intel.title or ""
        if intel.summary:
            text += f"\n{intel.summary}"

        if not text.strip():
            return {"intel_id": intel_id, "status": "empty_text"}

        # 使用 LLM 进行情感分析（同步调用需借助 asyncio）
        import asyncio
        try:
            sentiment_result = asyncio.run(analyze_sentiment(text))
            intel.sentiment = sentiment_result.get("sentiment", intel.sentiment)
            intel.updated_at = datetime.now(timezone.utc)
            session.commit()
            logger.info(f"情报情感分析完成: {intel_id} → {intel.sentiment}")
        except Exception as e:
            logger.warning(f"情报情感分析失败: {e}")
            session.rollback()

        return {"intel_id": intel_id, "status": "ok"}

    except Exception as exc:
        logger.error(f"情报分析异常: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def generate_daily_briefing(self):
    """生成每日简报：汇总当日情报，生成日报"""
    session = SyncSession()
    try:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # 获取当日情报
        intel_list = session.query(MarketIntelligence).filter(
            MarketIntelligence.published_at >= today_start
        ).order_by(MarketIntelligence.importance.desc()).limit(50).all()

        if not intel_list:
            logger.info("今日无新情报，跳过日报生成")
            return {"status": "skipped", "reason": "no_intelligence_today"}

        # 构建情报数据
        intelligence_data = []
        comp_names = {}
        for intel in intel_list:
            if intel.competitor_id not in comp_names:
                comp = session.query(Competitor).filter(Competitor.id == intel.competitor_id).first()
                comp_names[intel.competitor_id] = comp.name if comp else "未知竞品"

            intelligence_data.append({
                "title": intel.title,
                "summary": intel.summary or "",
                "category": intel.category or "未分类",
                "sentiment": intel.sentiment or "neutral",
                "importance": intel.importance or 3,
                "source_name": intel.source_name or "",
                "published_at": str(intel.published_at) if intel.published_at else None,
                "competitor_name": comp_names.get(intel.competitor_id, "未知"),
            })

        # 使用 LLM 生成报告
        import asyncio
        title = f"市场情报日报 — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        content = asyncio.run(generate_report(
            title=title,
            intelligence_data=intelligence_data,
            competitor_info=None,
            report_type="daily_briefing",
        ))

        # 保存报告
        report = AnalysisReport(
            title=title,
            content=content,
            status="completed",
            report_type="daily_briefing",
            generated_by="scheduled",
            ai_model=settings.OPENAI_MODEL,
            ai_prompt=f"Auto-generated daily briefing with {len(intelligence_data)} intelligence items",
            tags=["日报", "自动生成"],
        )
        session.add(report)
        session.commit()
        logger.info(f"日报生成完成: {report.id}")
        return {"status": "ok", "report_id": str(report.id)}

    except Exception as exc:
        logger.error(f"日报生成异常: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def generate_weekly_report(self):
    """生成每周分析报告：汇总本周情报，生成周报"""
    session = SyncSession()
    try:
        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # 获取本周情报
        intel_list = session.query(MarketIntelligence).filter(
            MarketIntelligence.published_at >= week_start
        ).order_by(MarketIntelligence.importance.desc()).limit(100).all()

        if not intel_list:
            logger.info("本周无新情报，跳过周报生成")
            return {"status": "skipped", "reason": "no_intelligence_this_week"}

        # 按竞品分组
        comp_names = {}
        intelligence_data = []
        for intel in intel_list:
            if intel.competitor_id not in comp_names:
                comp = session.query(Competitor).filter(Competitor.id == intel.competitor_id).first()
                comp_names[intel.competitor_id] = comp.name if comp else "未知竞品"

            intelligence_data.append({
                "title": intel.title,
                "summary": intel.summary or "",
                "category": intel.category or "未分类",
                "sentiment": intel.sentiment or "neutral",
                "importance": intel.importance or 3,
                "source_name": intel.source_name or "",
                "published_at": str(intel.published_at) if intel.published_at else None,
                "competitor_name": comp_names.get(intel.competitor_id, "未知"),
            })

        # 使用 LLM 生成周报
        import asyncio
        week_num = datetime.now(timezone.utc).isocalendar()[1]
        title = f"竞品分析周报 — 第 {week_num} 周 ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})"
        content = asyncio.run(generate_report(
            title=title,
            intelligence_data=intelligence_data,
            competitor_info=None,
            report_type="weekly_report",
        ))

        # 保存报告
        report = AnalysisReport(
            title=title,
            content=content,
            status="completed",
            report_type="weekly_report",
            generated_by="scheduled",
            ai_model=settings.OPENAI_MODEL,
            ai_prompt=f"Auto-generated weekly report with {len(intelligence_data)} intelligence items",
            tags=["周报", "自动生成"],
        )
        session.add(report)
        session.commit()
        logger.info(f"周报生成完成: {report.id}")
        return {"status": "ok", "report_id": str(report.id)}

    except Exception as exc:
        logger.error(f"周报生成异常: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()


@celery_app.task(bind=True)
def check_alert_rules(self):
    """检查预警规则：轮询所有活跃预警规则，匹配最近情报数据"""
    session = SyncSession()
    try:
        # 获取所有活跃预警规则
        rules = session.query(AlertRule).filter(AlertRule.is_active == True).all()

        if not rules:
            logger.info("无活跃预警规则")
            return {"status": "ok", "alerts_triggered": 0}

        # 获取最近 30 分钟内的新情报
        recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
        recent_intel = session.query(MarketIntelligence).filter(
            MarketIntelligence.published_at >= recent_cutoff
        ).all()

        alerts_triggered = 0

        for rule in rules:
            # 关键词匹配
            keywords = rule.keywords or []
            for intel in recent_intel:
                text = f"{intel.title} {intel.summary or ''}"
                matched_keywords = [kw for kw in keywords if kw.lower() in text.lower()]

                # 竞品匹配
                if rule.target_type == "competitor" and rule.target_id:
                    if str(intel.competitor_id) != str(rule.target_id):
                        continue

                # 如果关键词匹配或无关键词限制
                if matched_keywords or not keywords:
                    # 创建预警历史
                    severity = rule.severity or "medium"
                    # 如果匹配关键词中包含高危标记，提升严重级别
                    if any(kw in text.lower() for kw in ["融资", "ipo", "上市", "收购", "合并"]):
                        severity = "high"

                    alert = AlertHistory(
                        rule_id=rule.id,
                        title=f"[{rule.name}] 检测到新情报: {intel.title[:50]}",
                        content=f"匹配关键词: {', '.join(matched_keywords)}\n情报摘要: {intel.summary or intel.title}",
                        severity=severity,
                        triggered_by=intel.source_url or "",
                        source_data_id=intel.id,
                        triggered_at=datetime.now(timezone.utc),
                    )
                    session.add(alert)
                    alerts_triggered += 1
                    logger.info(f"预警触发: {rule.name} → {intel.title}")

        session.commit()
        logger.info(f"预警检查完成: {alerts_triggered} 条预警触发")
        return {"status": "ok", "alerts_triggered": alerts_triggered}

    except Exception as exc:
        logger.error(f"预警检查异常: {exc}")
        session.rollback()
        raise
    finally:
        session.close()


# ================================================================
#  LLM 选型专属报告
# ================================================================

SYSTEM_PROMPT_LLM_SELECTION = """你是一位专精于大语言模型（LLM）市场分析的资深技术顾问，\
拥有企业 AI 基础设施选型的丰富经验。

你的任务是基于提供的大模型竞品数据，生成一份结构清晰、数据驱动的《大模型选型评估报告》。

报告必须包含以下章节：

## 第一章：市场全景
- 当前大模型市场格局（国内/国际分类）
- 主要厂商近期重大动态（价格调整、新版本发布、融资情况）
- 市场竞争烈度评估

## 第二章：能力横向对比
- 以 Markdown 表格形式呈现各模型核心能力对比
  （上下文窗口、多模态支持、代码能力、推理能力、中文能力）
- 标注各项能力的领先者和明显短板

## 第三章：成本深度分析
- 以 Markdown 表格呈现 Token 定价（输入/输出分别列示，单位：元/百万 Token）
- 按月用量 1000 万 Token 测算各模型月度费用
- 性价比综合排名（成本/能力比）

## 第四章：场景适配建议
针对以下 5 个典型场景，各推荐 1~2 款最优模型并说明理由：
1. 代码生成与调试
2. 企业客服与对话
3. 文档处理与摘要
4. 复杂推理与分析
5. 通用场景兜底

## 第五章：风险评估
- 供应商稳定性分析（服务可用性、合规风险）
- 数据安全与隐私合规（重点关注境内合规要求）
- 供应商集中风险及多云备份建议

## 第六章：综合推荐
- 综合排名 TOP 3（附简要理由）
- 国产替代方案推荐（若有业务合规要求）
- 未来 3~6 个月的观察重点

**写作要求：**
- 语言：中文，专业但不晦涩
- 数据：尽量引用具体数字，避免模糊表述
- 观点：要有明确立场和推荐，不做模棱两可的陈述
- 长度：2000~4000 字
- 格式：使用 Markdown，层级清晰，关键数据加粗"""


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def generate_llm_selection_weekly(self):
    """每周一 08:00 自动生成大模型选型评估报告

    该任务通过 Celery Beat 调度，周期在 celery_app.py 的 beat_schedule 中配置。
    """
    session = SyncSession()
    try:
        # 1. 获取所有活跃大模型竞品（按 tier=direct 优先）
        comps = (
            session.query(Competitor)
            .filter(Competitor.is_active == True)
            .order_by(Competitor.tier, Competitor.name)
            .all()
        )

        if not comps:
            logger.info("无大模型竞品数据，跳过 LLM 选型报告生成")
            return {"status": "skipped", "reason": "no_competitors"}

        # 2. 构建竞品数据摘要（传给 LLM 作为上下文）
        comp_data_lines = []
        for c in comps:
            meta = c.metadata_ or {}
            line = (
                f"- **{c.name}**（{c.name_en or ''}）"
                f" | 旗舰模型: {meta.get('flagship_model', '未知')}"
                f" | 上下文窗口: {meta.get('context_window', '未知')} tokens"
                f" | 输入价格: {meta.get('input_price_per_1M', '?')} {meta.get('currency', 'USD')}/1M"
                f" | 输出价格: {meta.get('output_price_per_1M', '?')} {meta.get('currency', 'USD')}/1M"
                f" | 境内合规: {'✅' if meta.get('china_compliance') else '❌'}"
            )
            comp_data_lines.append(line)

        # 3. 获取最近 7 天高重要度情报
        week_start = datetime.now(timezone.utc) - timedelta(days=7)
        recent_intel = (
            session.query(MarketIntelligence)
            .filter(
                MarketIntelligence.importance >= 4,
                MarketIntelligence.published_at >= week_start,
            )
            .order_by(MarketIntelligence.importance.desc())
            .limit(30)
            .all()
        )
        intel_lines = []
        for intel in recent_intel:
            intel_lines.append(
                f"- [{intel.category or '动态'}] {intel.title}"
                + (f"（{intel.summary[:80]}…）" if intel.summary else "")
            )

        # 4. 构建用户提示词
        week_num = datetime.now(timezone.utc).isocalendar()[1]
        user_prompt = f"""请基于以下数据生成第 {week_num} 周大模型选型评估报告。

### 当前追踪的大模型竞品（共 {len(comps)} 家）
{chr(10).join(comp_data_lines) if comp_data_lines else "暂无数据"}

### 本周重要市场动态（共 {len(intel_lines)} 条）
{chr(10).join(intel_lines) if intel_lines else "本周暂无重要动态"}

请生成完整的选型评估报告，重点关注：
1. 本周市场价格或能力的重大变化
2. 当前性价比最优的 2~3 款模型
3. 国内合规场景下的首选推荐
"""

        # 5. 调用 LLM 生成报告内容
        import asyncio
        from app.services.llm import _call_llm  # noqa: 引用内部函数

        async def _gen():
            from openai import AsyncOpenAI
            from app.config import settings as s
            client = AsyncOpenAI(
                api_key=s.OPENAI_API_KEY,
                base_url=s.OPENAI_API_BASE or None,
            )
            resp = await client.chat.completions.create(
                model=s.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_LLM_SELECTION},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=4096,
            )
            return resp.choices[0].message.content or ""

        content = asyncio.run(_gen())

        # 6. 保存报告
        title = f"大模型选型评估报告 — 第 {week_num} 周 ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})"
        report = AnalysisReport(
            title=title,
            content=content,
            status="completed",
            report_type="llm_selection",
            generated_by="scheduled",
            ai_model=settings.OPENAI_MODEL,
            ai_prompt="LLM selection weekly report — auto generated",
            tags=["大模型选型", "周报", "自动生成"],
        )
        session.add(report)
        session.commit()
        logger.info(f"LLM 选型周报生成完成: {report.id}")
        return {"status": "ok", "report_id": str(report.id), "week": week_num}

    except Exception as exc:
        logger.error(f"LLM 选型周报生成异常: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()
# ================================================================
#  新增异步任务 1: 批量情报道分析
# ================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_intelligence_batch(self, intel_ids: list[str]):
    """批量对情报道进行情感分析和摘要提取
    
    每个情报独立调用 LLM，失败单个不影响整体。
    完成后自动写入数据库并推送通知。
    """
    session = SyncSession()
    try:
        total = len(intel_ids)
        success_count = 0
        fail_count = 0
        results = []

        for idx, intel_id in enumerate(intel_ids, 1):
            progress = int((idx / total) * 100)
            try:
                intel = session.query(MarketIntelligence).filter(
                    MarketIntelligence.id == intel_id
                ).first()
                if not intel:
                    results.append({"id": intel_id, "status": "not_found"})
                    fail_count += 1
                    continue

                text = f"{intel.title} {intel.summary or ''}"
                if not text.strip():
                    results.append({"id": intel_id, "status": "empty_text"})
                    fail_count += 1
                    continue

                # 情感分析
                sentiment_result = asyncio.run(analyze_sentiment(text))
                intel.sentiment = sentiment_result.get("sentiment", intel.sentiment)
                intel.sentiment_score = sentiment_result.get("sentiment_score", 0.5)

                # 摘要提取
                summary_result = asyncio.run(extract_summary(text))
                if summary_result.get("summary"):
                    intel.summary = summary_result["summary"]

                # 五维评分
                from app.services.llm_scorer import score_intelligence
                scores = score_intelligence(intel.title or "", intel.summary or "")
                intel.relevance_score = scores.get("relevance_score", intel.relevance_score)
                intel.timeliness_score = scores.get("timeliness_score", intel.timeliness_score)
                intel.actionability_score = scores.get("actionability_score", intel.actionability_score)

                intel.updated_at = datetime.now(timezone.utc)
                session.commit()
                results.append({"id": intel_id, "status": "ok"})
                success_count += 1
                logger.info(f"[{idx}/{total}] 情报 {intel_id} 分析完成")

            except Exception as e:
                fail_count += 1
                results.append({"id": intel_id, "status": "error", "error": str(e)[:200]})
                logger.error(f"情报 {intel_id} 分析失败: {e}")

        logger.info(f"批量分析完成: 成功 {success_count}/{total}, 失败 {fail_count}/{total}")
        return {
            "status": "completed",
            "total": total,
            "success": success_count,
            "failed": fail_count,
            "results": results,
        }

    except Exception as exc:
        logger.error(f"批量分析异常: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()


# ================================================================
#  新增异步任务 2: 异步报告生成
# ================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def generate_report_async(self, title: str, intel_ids: list[str], report_type: str = "daily_briefing"):
    """异步生成分析报告，完成后写入数据库并推送通知"""
    session = SyncSession()
    try:
        # 1. 加载情报数据
        intel_list = session.query(MarketIntelligence).filter(
            MarketIntelligence.id.in_(intel_ids)
        ).order_by(MarketIntelligence.importance.desc()).all()

        if not intel_list:
            return {"status": "skipped", "reason": "no_intelligence_found"}

        # 2. 构建情报数据
        intelligence_data = []
        comp_names = {}
        for intel in intel_list:
            if intel.competitor_id not in comp_names:
                comp = session.query(Competitor).filter(Competitor.id == intel.competitor_id).first()
                comp_names[intel.competitor_id] = comp.name if comp else "未知竞品"

            intelligence_data.append({
                "title": intel.title,
                "summary": intel.summary or "",
                "category": intel.category or "未分类",
                "sentiment": intel.sentiment or "neutral",
                "importance": intel.importance or 3,
                "source_name": intel.source_name or "",
                "published_at": str(intel.published_at) if intel.published_at else None,
                "competitor_name": comp_names.get(intel.competitor_id, "未知"),
            })

        # 3. 生成报告内容
        content = asyncio.run(generate_report(
            title=title,
            intelligence_data=intelligence_data,
            competitor_info=None,
            report_type=report_type,
        ))

        # 4. 保存报告
        report = AnalysisReport(
            title=title,
            content=content,
            status="completed",
            report_type=report_type,
            generated_by="manual",
            ai_model=settings.OPENAI_MODEL,
            ai_prompt=f"Manual report generation with {len(intelligence_data)} intelligence items",
            tags=[report_type, "手动生成"],
        )
        session.add(report)
        session.commit()

        logger.info(f"报告生成完成: {report.id} ({report_type})")
        return {"status": "ok", "report_id": str(report.id), "report_type": report_type}

    except Exception as exc:
        logger.error(f"报告生成异常: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()


# ================================================================
#  新增异步任务 3: 竞品深度分析
# ================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def deep_competitor_analysis(self, competitor_id: str):
    """异步竞品深度分析：结合历史情报生成 SWOT + 威胁评估"""
    session = SyncSession()
    try:
        # 1. 获取竞品信息
        comp = session.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not comp:
            return {"status": "error", "reason": "competitor_not_found"}

        # 2. 获取最近 90 天的情报
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        intel_list = session.query(MarketIntelligence).filter(
            MarketIntelligence.competitor_id == competitor_id,
            MarketIntelligence.published_at >= cutoff,
        ).order_by(MarketIntelligence.published_at.desc()).limit(200).all()

        if not intel_list:
            return {"status": "skipped", "reason": "no_intelligence_for_competitor"}

        # 3. 构建竞品上下文
        comp_data = {
            "name": comp.name,
            "tier": comp.tier,
            "description": comp.description or "",
            "website": comp.website or "",
            "headquarters": comp.headquarters or "",
            "founded_year": comp.founded_year,
            "employee_count": comp.employee_count,
            "funding_stage": comp.funding_stage,
            "total_funding": comp.total_funding,
            "tags": comp.tags or [],
            "metadata": comp.metadata_ or {},
        }

        intel_context = []
        for intel in intel_list:
            intel_context.append({
                "title": intel.title,
                "summary": intel.summary or "",
                "category": intel.category or "",
                "sentiment": intel.sentiment or "neutral",
                "importance": intel.importance or 3,
                "published_at": str(intel.published_at) if intel.published_at else None,
            })

        # 4. 调用 LLM 进行深度分析
        from app.services.llm_enhanced import analyze_competitor
        result = asyncio.run(analyze_competitor(
            comp_data,
            intel_context,
        ))

        # 5. 保存分析结果到 SentimentData 表
        from app.models import SentimentData
        sentiment_record = SentimentData(
            competitor_id=comp.id,
            sentiment_type="deep_analysis",
            sentiment_label=result.get("threat_level", "medium"),
            sentiment_score=result.get("threat_level") == "high" and 0.8 or 0.5,
            analysis_result=result,
            source="ai_deep_analysis",
            analyzed_at=datetime.now(timezone.utc),
        )
        session.add(sentiment_record)
        session.commit()

        logger.info(f"竞品深度分析完成: {comp.name} (威胁等级: {result.get('threat_level', 'unknown')})")
        return {
            "status": "ok",
            "competitor_id": str(comp.id),
            "competitor_name": comp.name,
            "threat_level": result.get("threat_level", "unknown"),
            "analysis_record_id": str(sentiment_record.id),
            "intelligence_count": len(intel_context),
        }

    except Exception as exc:
        logger.error(f"竞品深度分析异常: {exc}")
        raise self.retry(exc=exc)
    finally:
        session.close()