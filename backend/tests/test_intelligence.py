"""市场情报 API 测试 — CRUD / 统计 / 权限校验"""
import pytest

from tests.conftest import auth_headers


# 测试用例创建竞品的辅助函数
async def _create_competitor(client, token, name="情报关联竞品"):
    """创建一个竞品，返回其 ID"""
    resp = await client.post(
        "/api/v1/competitors/",
        json={"name": name, "tier": "direct"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# 测试用例创建情报的辅助函数
async def _create_intelligence(client, token, competitor_id, title="测试情报"):
    """创建一条市场情报，返回响应数据"""
    resp = await client.post(
        "/api/v1/intelligence/",
        json={
            "competitor_id": competitor_id,
            "title": title,
            "category": "product_update",
            "sentiment": "positive",
            "importance": 4,
            "summary": "竞品发布了新版本",
        },
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
class TestIntelligenceCRUD:
    """市场情报增删改查测试"""

    async def test_create_intelligence_as_analyst(self, client, analyst_token):
        """分析师创建情报"""
        comp_id = await _create_competitor(client, analyst_token)
        data = await _create_intelligence(client, analyst_token, comp_id, "新情报A")
        assert data["title"] == "新情报A"
        assert data["category"] == "product_update"
        assert data["sentiment"] == "positive"
        assert data["importance"] == 4

    async def test_create_intelligence_as_viewer_forbidden(self, client, viewer_token, analyst_token):
        """观察者不能创建情报"""
        comp_id = await _create_competitor(client, analyst_token)
        resp = await client.post(
            "/api/v1/intelligence/",
            json={"competitor_id": comp_id, "title": "不应创建"},
            headers=auth_headers(viewer_token),
        )
        assert resp.status_code == 403

    async def test_create_intelligence_with_nonexistent_competitor(self, client, analyst_token):
        """关联不存在的竞品时返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            "/api/v1/intelligence/",
            json={"competitor_id": fake_id, "title": "无关联"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 404
        assert "竞品不存在" in resp.json()["detail"]

    async def test_list_intelligence(self, client, admin_token, analyst_token):
        """获取情报列表"""
        comp_id = await _create_competitor(client, analyst_token)
        await _create_intelligence(client, analyst_token, comp_id, "列表情报1")
        await _create_intelligence(client, analyst_token, comp_id, "列表情报2")

        resp = await client.get("/api/v1/intelligence/", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    async def test_list_intelligence_filter_by_category(self, client, admin_token, analyst_token):
        """按分类筛选情报"""
        comp_id = await _create_competitor(client, analyst_token)
        await _create_intelligence(client, analyst_token, comp_id, "分类情报")

        resp = await client.get(
            "/api/v1/intelligence/?category=product_update",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["category"] == "product_update" for i in items)

    async def test_list_intelligence_filter_by_sentiment(self, client, admin_token, analyst_token):
        """按情感筛选情报"""
        comp_id = await _create_competitor(client, analyst_token)
        await _create_intelligence(client, analyst_token, comp_id, "情感情报")

        resp = await client.get(
            "/api/v1/intelligence/?sentiment=positive",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["sentiment"] == "positive" for i in items)

    async def test_list_intelligence_keyword_search(self, client, admin_token, analyst_token):
        """关键词搜索情报标题/摘要"""
        comp_id = await _create_competitor(client, analyst_token)
        await _create_intelligence(client, analyst_token, comp_id, "独家重磅新产品发布")

        resp = await client.get(
            "/api/v1/intelligence/?keyword=重磅",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any("重磅" in i["title"] for i in items)

    async def test_get_intelligence_detail(self, client, admin_token, analyst_token):
        """获取情报详情"""
        comp_id = await _create_competitor(client, analyst_token)
        created = await _create_intelligence(client, analyst_token, comp_id, "详情情报")

        resp = await client.get(
            f"/api/v1/intelligence/{created['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "详情情报"

    async def test_get_nonexistent_intelligence(self, client, admin_token):
        """获取不存在的情报返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/intelligence/{fake_id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_intelligence(self, client, analyst_token):
        """更新情报"""
        comp_id = await _create_competitor(client, analyst_token)
        created = await _create_intelligence(client, analyst_token, comp_id, "待更新情报")

        resp = await client.put(
            f"/api/v1/intelligence/{created['id']}",
            json={
                "competitor_id": comp_id,
                "title": "已更新情报",
                "importance": 5,
            },
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "已更新情报"
        assert resp.json()["importance"] == 5

    async def test_update_nonexistent_intelligence(self, client, analyst_token):
        """更新不存在的情报返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        # 需要有效的 competitor_id 才能通过 schema 校验
        comp_id = await _create_competitor(client, analyst_token)
        resp = await client.put(
            f"/api/v1/intelligence/{fake_id}",
            json={"competitor_id": comp_id, "title": "x"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 404

    async def test_delete_intelligence_as_admin(self, client, admin_token, analyst_token):
        """管理员删除情报"""
        comp_id = await _create_competitor(client, analyst_token)
        created = await _create_intelligence(client, analyst_token, comp_id, "待删除情报")

        resp = await client.delete(
            f"/api/v1/intelligence/{created['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert "已删除" in resp.json()["detail"]

    async def test_delete_intelligence_as_analyst_forbidden(self, client, analyst_token):
        """分析师不能删除情报"""
        comp_id = await _create_competitor(client, analyst_token)
        created = await _create_intelligence(client, analyst_token, comp_id, "分析师不能删")

        resp = await client.delete(
            f"/api/v1/intelligence/{created['id']}",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestIntelligenceStats:
    """情报统计接口测试"""

    async def test_stats_empty(self, client, admin_token):
        """空库时统计返回零值"""
        resp = await client.get("/api/v1/intelligence/stats", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["by_category"] == {}
        assert data["by_sentiment"] == {}

    async def test_stats_with_data(self, client, admin_token, analyst_token):
        """有数据时统计正确"""
        comp_id = await _create_competitor(client, analyst_token)
        await _create_intelligence(client, analyst_token, comp_id, "统计情报1")
        await _create_intelligence(client, analyst_token, comp_id, "统计情报2")

        resp = await client.get("/api/v1/intelligence/stats", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert "product_update" in data["by_category"]
        assert "positive" in data["by_sentiment"]


@pytest.mark.asyncio
class TestIntelligencePermission:
    """情报接口权限测试"""

    async def test_no_token_list_forbidden(self, client):
        """无 token 访问情报列表"""
        resp = await client.get("/api/v1/intelligence/")
        assert resp.status_code == 401

    async def test_no_token_create_forbidden(self, client):
        """无 token 创建情报"""
        resp = await client.post(
            "/api/v1/intelligence/",
            json={"competitor_id": "00000000-0000-0000-0000-000000000000", "title": "x"},
        )
        assert resp.status_code == 401
