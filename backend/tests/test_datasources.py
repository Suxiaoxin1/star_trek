"""数据源与采集数据 API 测试 — CRUD / 触发采集 / 统计 / 权限

注：触发采集接口会调用 Celery 任务，测试中使用 monkeypatch mock 任务对象，
避免真实连接 RabbitMQ broker。
"""
from datetime import datetime
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CollectedData
from tests.conftest import auth_headers


# 创建数据源的辅助函数
async def _create_datasource(client, token, name="测试数据源", **kwargs):
    """创建一个数据源，返回响应数据"""
    payload = {
        "name": name,
        "source_type": "rss",
        "url": "https://example.com/feed.xml",
        "crawl_interval_minutes": 60,
        "is_active": True,
    }
    payload.update(kwargs)
    resp = await client.post(
        "/api/v1/datasources/",
        json=payload,
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.json()


# 直接通过数据库创建采集数据的辅助函数
async def _create_collected_data(db_session: AsyncSession, source_id=None, title="采集文章"):
    """向数据库插入一条采集数据，返回对象

    source_id 来自 API JSON 响应（字符串），需转为 UUID 对象以匹配模型字段类型。
    """
    # 字符串 ID 转为 UUID 对象（API 返回的 JSON 中 id 是字符串）
    source_uuid = UUID(source_id) if isinstance(source_id, str) else source_id
    data = CollectedData(
        source_id=source_uuid,
        title=title,
        content="采集的原始内容",
        url="https://example.com/article/1",
        language="zh",
        collected_at=datetime.utcnow(),
        processed=False,
    )
    db_session.add(data)
    await db_session.flush()
    await db_session.refresh(data)
    return data


# Mock Celery 任务对象（带 .delay() 方法）
def _mock_celery_task(task_id="fake-task-id"):
    """构造一个模拟的 Celery 任务，返回带 id 属性的 MagicMock"""
    task = MagicMock()
    task.id = task_id
    return task


@pytest.mark.asyncio
class TestDatasourceCRUD:
    """数据源增删改查测试"""

    async def test_create_datasource_as_analyst(self, client, analyst_token):
        """分析师创建数据源"""
        data = await _create_datasource(client, analyst_token, "RSS 源")
        assert data["name"] == "RSS 源"
        assert data["source_type"] == "rss"
        assert data["is_active"] is True

    async def test_create_datasource_as_viewer_forbidden(self, client, viewer_token):
        """观察者不能创建数据源"""
        resp = await client.post(
            "/api/v1/datasources/",
            json={"name": "不应创建", "source_type": "rss"},
            headers=auth_headers(viewer_token),
        )
        assert resp.status_code == 403

    async def test_create_datasource_with_invalid_type(self, client, analyst_token):
        """非法 source_type 被 schema 拒绝"""
        resp = await client.post(
            "/api/v1/datasources/",
            json={"name": "非法类型", "source_type": "unknown"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 422

    async def test_list_datasources(self, client, admin_token, analyst_token):
        """获取数据源列表"""
        await _create_datasource(client, analyst_token, "列表数据源1")
        await _create_datasource(client, analyst_token, "列表数据源2")

        resp = await client.get("/api/v1/datasources/", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2

    async def test_list_datasources_filter_by_type(self, client, admin_token, analyst_token):
        """按类型筛选数据源"""
        await _create_datasource(client, analyst_token, "RSS源", source_type="rss")
        await _create_datasource(client, analyst_token, "API源", source_type="api")

        resp = await client.get(
            "/api/v1/datasources/?source_type=rss",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["source_type"] == "rss" for i in items)

    async def test_list_datasources_filter_by_active(self, client, admin_token, analyst_token):
        """按启用状态筛选"""
        await _create_datasource(client, analyst_token, "启用源", is_active=True)
        await _create_datasource(client, analyst_token, "停用源", is_active=False)

        resp = await client.get(
            "/api/v1/datasources/?is_active=true",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["is_active"] is True for i in items)

    async def test_get_datasource_detail(self, client, admin_token, analyst_token):
        """获取数据源详情"""
        created = await _create_datasource(client, analyst_token, "详情数据源")

        resp = await client.get(
            f"/api/v1/datasources/{created['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "详情数据源"

    async def test_get_nonexistent_datasource(self, client, admin_token):
        """获取不存在的数据源返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/datasources/{fake_id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_datasource(self, client, analyst_token):
        """更新数据源"""
        created = await _create_datasource(client, analyst_token, "待更新数据源")

        resp = await client.put(
            f"/api/v1/datasources/{created['id']}",
            json={"name": "已更新数据源", "is_active": False},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "已更新数据源"
        assert data["is_active"] is False

    async def test_delete_datasource_as_admin(self, client, admin_token, analyst_token):
        """管理员删除数据源"""
        created = await _create_datasource(client, analyst_token, "待删除数据源")

        resp = await client.delete(
            f"/api/v1/datasources/{created['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    async def test_delete_datasource_as_analyst_forbidden(self, client, analyst_token):
        """分析师不能删除数据源"""
        created = await _create_datasource(client, analyst_token, "分析师不能删")

        resp = await client.delete(
            f"/api/v1/datasources/{created['id']}",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestDatasourceCrawl:
    """触发采集接口测试（mock Celery）"""

    async def test_trigger_crawl_single(self, client, analyst_token, monkeypatch):
        """触发单个数据源采集"""
        created = await _create_datasource(client, analyst_token, "单采集源")

        # mock crawl_single_source.delay 返回任务对象
        mock_task = MagicMock()
        mock_task.delay.return_value = _mock_celery_task("task-single-123")
        monkeypatch.setattr("app.routes.datasources.crawl_single_source", mock_task)

        resp = await client.post(
            f"/api/v1/datasources/{created['id']}/crawl",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == "task-single-123"
        assert data["status"] == "dispatched"
        mock_task.delay.assert_called_once_with(created["id"])

    async def test_trigger_crawl_inactive_source(self, client, analyst_token):
        """触发已禁用数据源采集返回 400"""
        created = await _create_datasource(client, analyst_token, "禁用源", is_active=False)

        resp = await client.post(
            f"/api/v1/datasources/{created['id']}/crawl",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 400
        assert "禁用" in resp.json()["detail"]

    async def test_trigger_crawl_nonexistent_source(self, client, analyst_token):
        """触发不存在数据源采集返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            f"/api/v1/datasources/{fake_id}/crawl",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 404

    async def test_trigger_crawl_all(self, client, analyst_token, monkeypatch):
        """触发全部数据源采集"""
        mock_task = MagicMock()
        mock_task.delay.return_value = _mock_celery_task("task-all-456")
        monkeypatch.setattr("app.routes.datasources.crawl_all_sources", mock_task)

        resp = await client.post(
            "/api/v1/datasources/crawl-all",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        assert resp.json()["task_id"] == "task-all-456"
        mock_task.delay.assert_called_once()

    async def test_trigger_crawl_by_type(self, client, analyst_token, monkeypatch):
        """按类型触发采集"""
        mock_task = MagicMock()
        mock_task.delay.return_value = _mock_celery_task("task-type-789")
        monkeypatch.setattr("app.routes.datasources.crawl_sources_by_type", mock_task)

        resp = await client.post(
            "/api/v1/datasources/crawl-by-type/rss",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_type"] == "rss"
        assert data["task_id"] == "task-type-789"
        mock_task.delay.assert_called_once_with("rss")

    async def test_trigger_crawl_by_invalid_type(self, client, analyst_token):
        """按非法类型触发采集返回 400"""
        resp = await client.post(
            "/api/v1/datasources/crawl-by-type/unknown",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 400

    async def test_trigger_crawl_as_viewer_forbidden(self, client, viewer_token, analyst_token):
        """观察者不能触发采集"""
        created = await _create_datasource(client, analyst_token, "权限源")

        resp = await client.post(
            f"/api/v1/datasources/{created['id']}/crawl",
            headers=auth_headers(viewer_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestDatasourceStats:
    """数据源统计接口测试"""

    async def test_stats_empty(self, client, admin_token):
        """空库时统计返回零值"""
        resp = await client.get("/api/v1/datasources/stats", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["active"] == 0
        assert data["by_type"] == {}

    async def test_stats_with_data(self, client, admin_token, analyst_token):
        """有数据时统计正确"""
        await _create_datasource(client, analyst_token, "统计源1", source_type="rss", is_active=True)
        await _create_datasource(client, analyst_token, "统计源2", source_type="api", is_active=False)

        resp = await client.get("/api/v1/datasources/stats", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert data["active"] >= 1
        assert "rss" in data["by_type"]


@pytest.mark.asyncio
class TestCollectedData:
    """采集数据查看测试"""

    async def test_collected_stats_empty(self, client, admin_token):
        """空库时采集数据统计返回零值"""
        resp = await client.get("/api/v1/collected-data/stats", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["processed"] == 0

    async def test_collected_stats_with_data(self, client, admin_token, analyst_token, db_session):
        """有数据时统计正确"""
        source = await _create_datasource(client, analyst_token, "采集统计源")
        await _create_collected_data(db_session, source["id"], "采集文章1")
        await _create_collected_data(db_session, source["id"], "采集文章2")

        resp = await client.get("/api/v1/collected-data/stats", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert source["name"] in data["by_source"]

    async def test_list_collected_data(self, client, admin_token, analyst_token, db_session):
        """获取采集数据列表"""
        source = await _create_datasource(client, analyst_token, "列表采集源")
        await _create_collected_data(db_session, source["id"], "列表文章1")
        await _create_collected_data(db_session, source["id"], "列表文章2")

        resp = await client.get("/api/v1/collected-data/", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2

    async def test_list_collected_filter_by_source(self, client, admin_token, analyst_token, db_session):
        """按数据源筛选采集数据"""
        source1 = await _create_datasource(client, analyst_token, "源A")
        source2 = await _create_datasource(client, analyst_token, "源B")
        await _create_collected_data(db_session, source1["id"], "源A文章")
        await _create_collected_data(db_session, source2["id"], "源B文章")

        resp = await client.get(
            f"/api/v1/collected-data/?source_id={source1['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["source_id"] == source1["id"] for i in items)

    async def test_list_collected_keyword_search(self, client, admin_token, analyst_token, db_session):
        """关键词搜索采集数据标题"""
        source = await _create_datasource(client, analyst_token, "关键词源")
        await _create_collected_data(db_session, source["id"], "重磅独家新闻")

        resp = await client.get(
            "/api/v1/collected-data/?keyword=重磅",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any("重磅" in (i["title"] or "") for i in items)

    async def test_get_collected_detail(self, client, admin_token, analyst_token, db_session):
        """获取采集数据详情"""
        source = await _create_datasource(client, analyst_token, "详情采集源")
        data = await _create_collected_data(db_session, source["id"], "详情文章")

        resp = await client.get(
            f"/api/v1/collected-data/{data.id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "详情文章"

    async def test_get_nonexistent_collected(self, client, admin_token):
        """获取不存在的采集数据返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/collected-data/{fake_id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 404

    async def test_mark_collected_processed(self, client, analyst_token, db_session):
        """标记采集数据为已处理"""
        source = await _create_datasource(client, analyst_token, "处理源")
        data = await _create_collected_data(db_session, source["id"], "待处理文章")

        resp = await client.put(
            f"/api/v1/collected-data/{data.id}/process",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        assert "已处理" in resp.json()["message"]

    async def test_mark_processed_as_viewer_forbidden(self, client, viewer_token, analyst_token, db_session):
        """观察者不能标记已处理"""
        source = await _create_datasource(client, analyst_token, "权限处理源")
        data = await _create_collected_data(db_session, source["id"], "权限文章")

        resp = await client.put(
            f"/api/v1/collected-data/{data.id}/process",
            headers=auth_headers(viewer_token),
        )
        assert resp.status_code == 403

    async def test_delete_collected_as_admin(self, client, admin_token, analyst_token, db_session):
        """管理员删除采集数据"""
        source = await _create_datasource(client, analyst_token, "删除源")
        data = await _create_collected_data(db_session, source["id"], "待删除文章")

        resp = await client.delete(
            f"/api/v1/collected-data/{data.id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    async def test_delete_collected_as_analyst_forbidden(self, client, analyst_token, db_session):
        """分析师不能删除采集数据"""
        source = await _create_datasource(client, analyst_token, "分析师删除源")
        data = await _create_collected_data(db_session, source["id"], "不能删")

        resp = await client.delete(
            f"/api/v1/collected-data/{data.id}",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestDatasourcesPermission:
    """数据源接口权限测试"""

    async def test_no_token_list_datasources_forbidden(self, client):
        """无 token 访问数据源列表"""
        resp = await client.get("/api/v1/datasources/")
        assert resp.status_code == 401

    async def test_no_token_stats_forbidden(self, client):
        """无 token 访问数据源统计"""
        resp = await client.get("/api/v1/datasources/stats")
        assert resp.status_code == 401

    async def test_no_token_collected_list_forbidden(self, client):
        """无 token 访问采集数据列表"""
        resp = await client.get("/api/v1/collected-data/")
        assert resp.status_code == 401
