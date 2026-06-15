"""数据采集任务"""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def crawl_single_source(self, source_id: str):
    """采集单个数据源"""
    # TODO: 实现数据源采集逻辑
    return {"source_id": source_id, "status": "ok", "items": 0}


@celery_app.task(bind=True)
def crawl_all_sources(self):
    """采集所有数据源"""
    # TODO: 获取所有启用的数据源并逐个采集
    return {"status": "ok", "sources_processed": 0}
