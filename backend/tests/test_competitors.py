"""竞品管理 API 测试"""
import pytest


@pytest.mark.asyncio
class TestCompetitors:

    async def test_create_competitor_as_analyst(self, client, analyst_token):
        """分析师创建竞品"""
        resp = await client.post(
            "/api/v1/competitors/",
            json={
                "name": "竞品A",
                "name_en": "CompetitorA",
                "website": "https://a.com",
                "tier": "direct",
                "description": "直接竞品",
                "headquarters": "北京",
            },
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "竞品A"
        assert data["tier"] == "direct"
        return data["id"]

    async def test_create_competitor_as_viewer_forbidden(self, client, viewer_token):
        """观察者不能创建竞品"""
        resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "不应创建的竞品", "tier": "direct"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    async def test_list_competitors(self, client, admin_token, analyst_token):
        """获取竞品列表"""
        # 先创建一条数据
        await client.post(
            "/api/v1/competitors/",
            json={"name": "列表测试竞品", "tier": "indirect"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        resp = await client.get(
            "/api/v1/competitors/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_list_competitors_with_filter(self, client, admin_token, analyst_token):
        """筛选竞品列表"""
        await client.post(
            "/api/v1/competitors/",
            json={"name": "筛选测试直接竞品", "tier": "direct"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        resp = await client.get(
            "/api/v1/competitors/?tier=direct",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["tier"] == "direct" for i in items)

    async def test_get_competitor_detail(self, client, admin_token, analyst_token):
        """获取竞品详情"""
        create_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "详情测试竞品", "tier": "potential"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.get(
            f"/api/v1/competitors/{comp_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "详情测试竞品"

    async def test_update_competitor(self, client, analyst_token):
        """更新竞品"""
        create_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "待更新竞品", "tier": "direct"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.put(
            f"/api/v1/competitors/{comp_id}",
            json={"name": "已更新竞品", "headquarters": "上海"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "已更新竞品"

    async def test_soft_delete_competitor_as_admin(self, client, admin_token, analyst_token):
        """管理员软删除竞品"""
        create_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "待删除竞品"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/competitors/{comp_id}?soft=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "软删除" in resp.json()["detail"]

    async def test_delete_competitor_as_analyst_forbidden(self, client, analyst_token):
        """分析师不能删除竞品"""
        create_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "分析师不能删"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/competitors/{comp_id}",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 403

    async def test_create_product(self, client, analyst_token):
        """创建产品"""
        comp_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "有产品的竞品"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = comp_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/competitors/{comp_id}/products",
            json={"name": "核心产品", "category": "SaaS", "pricing_model": "订阅制"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "核心产品"

    async def test_create_feature(self, client, analyst_token):
        """创建功能点"""
        comp_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "有功能的竞品"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = comp_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/competitors/{comp_id}/features",
            json={
                "category": "AI",
                "feature_name": "智能分析",
                "support_level": "full",
            },
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["feature_name"] == "智能分析"

    async def test_record_pricing(self, client, analyst_token):
        """记录价格变动"""
        comp_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "有价格的竞品"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = comp_resp.json()["id"]
        resp = await client.post(
            f"/api/v1/competitors/{comp_id}/pricing-history",
            json={
                "plan_name": "企业版",
                "old_price": 99,
                "new_price": 199,
                "currency": "CNY",
                "billing_cycle": "月",
                "change_type": "涨价",
                "detected_at": "2026-01-15T10:00:00",
            },
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["new_price"] == 199

    async def test_404_nonexistent_competitor(self, client, admin_token):
        """访问不存在的竞品"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/competitors/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404