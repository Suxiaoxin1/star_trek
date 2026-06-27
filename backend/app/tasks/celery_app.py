"""Celery 应用配置"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "competitive_intel",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.crawler",
        "app.tasks.ai_analysis",
    ],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,       # 单任务超时 30 分钟
    task_soft_time_limit=25 * 60,  # 软超时 25 分钟
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,
)

# ======================= 定时任务调度 =======================
celery_app.conf.beat_schedule = {
    # 每小时：竞品官网监控
    "crawl-competitor-websites": {
        "task": "app.tasks.crawler.crawl_all_sources",
        "schedule": crontab(minute=0, hour="*"),
        "options": {"queue": "crawler"},
    },
    # 每日 08:00：生成日报
    "generate-daily-briefing": {
        "task": "app.tasks.ai_analysis.generate_daily_briefing",
        "schedule": crontab(minute=0, hour=8),
    },
    # 每周一 09:00：生成周报
    "generate-weekly-report": {
        "task": "app.tasks.ai_analysis.generate_weekly_report",
        "schedule": crontab(minute=0, hour=9, day_of_week=1),
    },
    # 每 30 分钟：预警检查
    "check-alert-rules": {
        "task": "app.tasks.ai_analysis.check_alert_rules",
        "schedule": crontab(minute="*/30"),
    },
    # 每周一 08:00：LLM 选型评估周报（早于常规周报，供决策参考）
    "generate-llm-selection-weekly": {
        "task": "app.tasks.ai_analysis.generate_llm_selection_weekly",
        "schedule": crontab(minute=0, hour=8, day_of_week=1),
    },
}
