"""数据采集任务 —— RSS / Web Scraper / API 数据源采集"""
import hashlib
import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

import httpx
import feedparser
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import DataSource, CollectedData
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Celery prefork 模式下 fork 后连接池会失效，使用 NullPool 避免连接复用问题
from sqlalchemy.pool import NullPool

_engine = None
_SessionLocal = None


def _get_engine():
    """延迟初始化引擎，确保在 worker 子进程内创建而非 fork 前创建"""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL_SYNC,
            poolclass=NullPool,  # 每次请求新建连接，避免 fork 后连接池失效
        )
        _SessionLocal = sessionmaker(bind=_engine)
    return _engine


@contextmanager
def get_sync_session():
    """获取同步数据库会话的上下文管理器"""
    _get_engine()
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _content_hash(text: str) -> str:
    """计算内容 SHA256 哈希，用于去重"""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _save_collected_data(session, source_id: str, items: list[dict]) -> int:
    """
    批量保存采集数据，自动去重。
    返回实际新增条数。
    """
    saved = 0
    for item in items:
        title = item.get("title", "")
        content = item.get("content", "")
        url = item.get("url", "")
        # 哈希：url + title + content 拼接后取 SHA256
        hash_input = f"{url}|{title}|{content[:2000]}"
        content_hash = _content_hash(hash_input)

        # 去重检查
        existing = session.query(CollectedData).filter(
            CollectedData.source_id == source_id,
            CollectedData.content_hash == content_hash,
        ).first()
        if existing:
            continue

        entry = CollectedData(
            source_id=source_id,
            title=title,
            content=content,
            content_hash=content_hash,
            url=url,
            language=item.get("language", "zh"),
            raw_data=item.get("raw_data", {}),
            collected_at=item.get("collected_at", datetime.now(timezone.utc)),
            processed=False,
        )
        session.add(entry)
        saved += 1

    session.commit()
    return saved


# ======================= RSS 采集 =======================
def _crawl_rss(source: DataSource) -> list[dict]:
    """RSS / Atom Feed 采集"""
    items = []
    try:
        feed = feedparser.parse(source.url)
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            # 内容优先级：summary > description > content
            content = ""
            if hasattr(entry, "summary"):
                content = entry.summary
            elif hasattr(entry, "description"):
                content = entry.description
            elif hasattr(entry, "content"):
                content = entry.content[0].get("value", "") if entry.content else ""

            # 清理 HTML 标签
            if content:
                soup = BeautifulSoup(content, "lxml")
                content = soup.get_text(separator="\n", strip=True)

            published = entry.get("published_parsed") or entry.get("updated_parsed")
            collected_at = (
                datetime(*published[:6], tzinfo=timezone.utc) if published
                else datetime.now(timezone.utc)
            )

            items.append({
                "title": title,
                "content": content,
                "url": link,
                "language": source.crawl_config.get("language", "zh"),
                "raw_data": {
                    "feed_title": feed.feed.get("title", ""),
                    "feed_link": feed.feed.get("link", ""),
                    "author": entry.get("author", ""),
                    "tags": [t.get("term", "") for t in entry.get("tags", [])],
                },
                "collected_at": collected_at,
            })
    except Exception as e:
        logger.error(f"RSS 采集失败 [{source.name}]: {e}")
    return items


# ======================= Web Scraper 采集 =======================
def _crawl_web_scraper(source: DataSource) -> list[dict]:
    """Web 页面爬取，支持 CSS 选择器配置"""
    items = []
    config = source.crawl_config or {}
    selectors = config.get("selectors", {})
    headers = config.get("headers", {})
    timeout = config.get("timeout", 30)
    max_pages = config.get("max_pages", 1)

    title_selector = selectors.get("title", "h1")
    content_selector = selectors.get("content", "article, .content, .post-body, main")
    link_selector = selectors.get("links", "")

    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    request_headers = {**default_headers, **headers}

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
            # 如果配置了链接选择器，先抓列表页再逐个抓详情
            urls_to_crawl = []
            if link_selector:
                for page_num in range(1, max_pages + 1):
                    page_url = source.url
                    if max_pages > 1 and "{page}" in source.url:
                        page_url = source.url.replace("{page}", str(page_num))
                    resp = client.get(page_url, headers=request_headers)
                    soup = BeautifulSoup(resp.text, "lxml")
                    links = soup.select(link_selector)
                    for link_el in links:
                        href = link_el.get("href", "")
                        if href and not href.startswith("#"):
                            # 补全相对路径
                            if not href.startswith("http"):
                                from urllib.parse import urljoin
                                href = urljoin(source.url, href)
                            urls_to_crawl.append(href)
            else:
                urls_to_crawl = [source.url]

            # 抓取详情页
            for url in urls_to_crawl[:50]:  # 限制最大数量防止过载
                try:
                    resp = client.get(url, headers=request_headers)
                    soup = BeautifulSoup(resp.text, "lxml")

                    title_el = soup.select_one(title_selector)
                    title = title_el.get_text(strip=True) if title_el else soup.title.string or ""

                    content_el = soup.select_one(content_selector)
                    content = content_el.get_text(separator="\n", strip=True) if content_el else ""

                    items.append({
                        "title": title.strip(),
                        "content": content.strip(),
                        "url": url,
                        "language": config.get("language", "zh"),
                        "raw_data": {
                            "source_name": source.name,
                            "crawl_type": "web_scraper",
                        },
                        "collected_at": datetime.now(timezone.utc),
                    })
                except Exception as e:
                    logger.warning(f"Web 页面抓取失败 [{url}]: {e}")

    except Exception as e:
        logger.error(f"Web Scraper 采集失败 [{source.name}]: {e}")
    return items


# ======================= API 采集 =======================
def _crawl_api(source: DataSource) -> list[dict]:
    """API 数据源采集（REST API 等）"""
    items = []
    config = source.api_config or {}
    endpoint = config.get("endpoint", source.url)
    headers = config.get("headers", {})
    params = config.get("params", {})
    timeout = config.get("timeout", 30)

    # 数据映射：API 返回 JSON → CollectedData 字段
    field_mapping = config.get("field_mapping", {})
    title_field = field_mapping.get("title", "title")
    content_field = field_mapping.get("content", "content")
    url_field = field_mapping.get("url", "url")
    date_field = field_mapping.get("date", "published_at")
    items_path = config.get("items_path", "")  # e.g. "data.items"

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(endpoint, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()

            # 按路径提取列表
            if items_path:
                for key in items_path.split("."):
                    data = data.get(key, data)

            if isinstance(data, list):
                for item in data:
                    title = str(item.get(title_field, ""))
                    content = str(item.get(content_field, ""))
                    url = str(item.get(url_field, ""))
                    date_val = item.get(date_field)

                    collected_at = datetime.now(timezone.utc)
                    if isinstance(date_val, str):
                        try:
                            collected_at = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                        except ValueError:
                            pass

                    items.append({
                        "title": title,
                        "content": content,
                        "url": url,
                        "language": config.get("language", "zh"),
                        "raw_data": item,
                        "collected_at": collected_at,
                    })

    except Exception as e:
        logger.error(f"API 采集失败 [{source.name}]: {e}")
    return items


# ======================= Celery 任务 =======================
CRAWL_HANDLER = {
    "rss": _crawl_rss,
    "web_scraper": _crawl_web_scraper,
    "api": _crawl_api,
    "news": _crawl_rss,  # news 类型复用 RSS 逻辑
}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_single_source(self, source_id: str):
    """采集单个数据源"""
    with get_sync_session() as session:
        try:
            source = session.query(DataSource).filter(DataSource.id == source_id).first()
            if not source:
                logger.warning(f"数据源不存在: {source_id}")
                return {"source_id": source_id, "status": "not_found", "items": 0}

            if not source.is_active:
                logger.info(f"数据源已禁用: {source.name}")
                return {"source_id": source_id, "status": "disabled", "items": 0}

            handler = CRAWL_HANDLER.get(source.source_type)
            if not handler:
                logger.warning(f"不支持的数据源类型: {source.source_type}")
                return {"source_id": source_id, "status": "unsupported_type", "items": 0}

            logger.info(f"开始采集: {source.name} [{source.source_type}] → {source.url}")
            raw_items = handler(source)

            # 保存并去重
            saved_count = _save_collected_data(session, str(source.id), raw_items)

            # 更新数据源状态
            source.last_crawled_at = datetime.now(timezone.utc)
            source.last_status = "success"
            session.commit()

            logger.info(f"采集完成: {source.name}, 原始 {len(raw_items)} 条, 新增 {saved_count} 条")
            return {"source_id": source_id, "status": "ok", "items": saved_count}

        except Exception as exc:
            session.rollback()
            # 更新失败状态
            try:
                source = session.query(DataSource).filter(DataSource.id == source_id).first()
                if source:
                    source.last_crawled_at = datetime.now(timezone.utc)
                    source.last_status = "failed"
                    session.commit()
            except Exception:
                pass

            logger.error(f"采集异常: {exc}")
            raise self.retry(exc=exc)


@celery_app.task(bind=True)
def crawl_all_sources(self):
    """采集所有启用的数据源"""
    with get_sync_session() as session:
        sources = session.query(DataSource).filter(DataSource.is_active == True).all()
        source_ids = [str(s.id) for s in sources]

        # 逐个下发子任务
        results = []
        for sid in source_ids:
            result = crawl_single_source.delay(sid)
            results.append(str(result.id))

        logger.info(f"下发采集任务: {len(source_ids)} 个数据源")
        return {"status": "ok", "sources_processed": len(source_ids), "task_ids": results}


@celery_app.task(bind=True)
def crawl_sources_by_type(self, source_type: str):
    """按类型采集数据源"""
    with get_sync_session() as session:
        sources = session.query(DataSource).filter(
            DataSource.is_active == True,
            DataSource.source_type == source_type,
        ).all()
        source_ids = [str(s.id) for s in sources]

        results = []
        for sid in source_ids:
            result = crawl_single_source.delay(sid)
            results.append(str(result.id))

        return {"status": "ok", "source_type": source_type, "count": len(source_ids), "task_ids": results}


# ================================================================
#  采集后自动转化为情报
# ================================================================

def _auto_convert_to_intelligence(session, collected_items, source):
    from app.models import MarketIntelligence, Competitor

    converted = 0
    all_comps = session.query(Competitor).filter(
        Competitor.is_active == True
    ).all()
    comp_map = {}
    for comp in all_comps:
        comp_map[comp.name.lower()] = comp
        if comp.name_en:
            comp_map[comp.name_en.lower()] = comp

    high_imp_kws = ['融资', 'IPO', '上市', '收购', '合并', '重大', '突破', '制裁']
    med_imp_kws = ['更新', '版本', '新功能']

    for item in collected_items:
        title = item.get('title', '')
        content = item.get('content', '')
        url = item.get('url', '')
        raw_data = item.get('raw_data', {})
        tags = raw_data.get('tags', [])
        collected_at = item.get('collected_at', datetime.now(timezone.utc))

        matched_comp_id = None
        text_lower = f'{title} {content}'.lower()
        for name_lower, comp in comp_map.items():
            if len(name_lower) >= 2 and name_lower in text_lower:
                matched_comp_id = comp.id
                break

        category = '行业动态'
        if tags:
            cat_kws = [t for t in tags if t in ['产品发布', '融资', '招聘', '合作', '诉讼', '政策', '技术突破']]
            if cat_kws:
                category = cat_kws[0]

        importance = 3
        for kw in high_imp_kws:
            if kw in title or kw in content:
                importance = 5
                break
        else:
            for kw in med_imp_kws:
                if kw in title:
                    importance = 4
                    break

        summary = content[:200] + '...' if len(content) > 200 else content

        intel = MarketIntelligence(
            competitor_id=matched_comp_id,
            title=title,
            summary=summary,
            category=category,
            sentiment='neutral',
            importance=importance,
            source_name=source.name,
            source_url=url,
            source_type=source.source_type,
            published_at=collected_at,
            raw_data=raw_data,
        )
        session.add(intel)
        converted += 1

    if converted > 0:
        session.commit()
        logger.info(f'Auto-converted {converted} items to intelligence (source: {source.name})')

    return converted


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_single_source_and_convert(self, source_id: str):
    with get_sync_session() as session:
        try:
            source = session.query(DataSource).filter(DataSource.id == source_id).first()
            if not source:
                logger.warning(f'Source not found: {source_id}')
                return {{'source_id': source_id, 'status': 'not_found', 'items': 0, 'intelligences': 0}}

            if not source.is_active:
                logger.info(f'Source disabled: {{source.name}}')
                return {{'source_id': source_id, 'status': 'disabled', 'items': 0, 'intelligences': 0}}

            handler = CRAWL_HANDLER.get(source.source_type)
            if not handler:
                logger.warning(f'Unsupported source type: {{source.source_type}}')
                return {{'source_id': source_id, 'status': 'unsupported_type', 'items': 0, 'intelligences': 0}}

            logger.info(f'Starting crawl: {{source.name}} [{{source.source_type}}] -> {{source.url}}')
            raw_items = handler(source)

            saved_count = _save_collected_data(session, str(source.id), raw_items)
            intel_count = _auto_convert_to_intelligence(session, raw_items, source)

            source.last_crawled_at = datetime.now(timezone.utc)
            source.last_status = 'success'
            source.items_collected = (source.items_collected or 0) + saved_count
            session.commit()

            logger.info(f'Crawl done: {{source.name}}, raw={{len(raw_items)}}, new={{saved_count}}, intel={{intel_count}}')
            return {{
                'source_id': source_id,
                'status': 'ok',
                'items': saved_count,
                'intelligences': intel_count,
            }}

        except Exception as exc:
            session.rollback()
            try:
                source = session.query(DataSource).filter(DataSource.id == source_id).first()
                if source:
                    source.last_crawled_at = datetime.now(timezone.utc)
                    source.last_status = 'failed'
                    session.commit()
            except Exception:
                pass

            logger.error(f'Crawl exception: {{exc}}')
            raise self.retry(exc=exc)
