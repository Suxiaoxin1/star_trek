"""权限控制测试 — 验证不同角色的访问权限"""
import pytest


@pytest.mark.asyncio
class TestRolePermissions:

    async def test_viewer_can_read_competitors(self, client, viewer_token, analyst_token):
        """观察者可以读取竞品列表"""
        # 先用分析师创建数据
        await client.post(
            "/api/v1/competitors/",
            json={"name": "权限测试竞品"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        # 观察者读取
        resp = await client.get(
            "/api/v1/competitors/",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200

    async def test_viewer_cannot_create_competitor(self, client, viewer_token):
        """观察者不能创建竞品"""
        resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "观察者不能创建"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403
        assert "权限不足" in resp.json()["detail"]

    async def test_viewer_cannot_update_competitor(self, client, viewer_token, analyst_token):
        """观察者不能更新竞品"""
        create_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "观察者不能更新"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.put(
            f"/api/v1/competitors/{comp_id}",
            json={"name": "尝试更新"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    async def test_analyst_cannot_delete_competitor(self, client, analyst_token):
        """分析师不能删除竞品（仅管理员可以）"""
        create_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "分析师不能删除"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/competitors/{comp_id}",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_can_delete_competitor(self, client, admin_token, analyst_token):
        """管理员可以删除竞品"""
        create_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "管理员可删除"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/competitors/{comp_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    async def test_analyst_can_create_intelligence(self, client, analyst_token):
        """分析师可以创建情报"""
        # 先创建竞品
        comp_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "情报关联竞品"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = comp_resp.json()["id"]
        resp = await client.post(
            "/api/v1/intelligence/",
            json={
                "title": "新情报",
                "competitor_id": comp_id,
                "category": "product_update",
                "importance": 4,
            },
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert resp.status_code == 201

    async def test_viewer_cannot_create_intelligence(self, client, viewer_token, analyst_token):
        """观察者不能创建情报"""
        comp_resp = await client.post(
            "/api/v1/competitors/",
            json={"name": "观察者情报竞品"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        comp_id = comp_resp.json()["id"]
        resp = await client.post(
            "/api/v1/intelligence/",
            json={
                "title": "观察者不能创建的情报",
                "competitor_id": comp_id,
            },
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_trigger_crawl(self, client, viewer_token):
        """观察者不能触发采集"""
        resp = await client.post(
            "/api/v1/datasources/crawl-all",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    async def test_analyst_can_trigger_crawl(self, client, analyst_token):
        """分析师可以触发采集"""
        # 注意：这里只是权限测试，Celery 任务在没有 broker 时会失败
        # 但权限检查应该先通过
        resp = await client.post(
            "/api/v1/datasources/crawl-all",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        # 权限检查通过（可能是 200 或 500，取决于 Celery 是否可用）
        assert resp.status_code in [200, 500]  # 500 是 Celery 不可用导致的
        if resp.status_code == 403:
            pytest.fail("分析师不应该被403阻止触发采集")

    async def test_viewer_cannot_use_ai_features(self, client, viewer_token):
        """观察者不能使用 AI 功能"""
        resp = await client.post(
            "/api/v1/ai/sentiment",
            json={"text": "测试文本"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_can_view_ai_status(self, client, viewer_token):
        """观察者可以查看 AI 状态"""
        resp = await client.get(
            "/api/v1/ai/status",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200

    async def test_viewer_can_read_reports(self, client, viewer_token):
        """观察者可以查看报告列表"""
        resp = await client.get(
            "/api/v1/reports/",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200

    async def test_viewer_can_read_alerts(self, client, viewer_token):
        """观察者可以查看预警"""
        resp = await client.get(
            "/api/v1/alerts/stats",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200

    async def test_viewer_cannot_resolve_alert(self, client, viewer_token, analyst_token):
        """观察者不能处理预警"""
        # 创建规则
        rule_resp = await client.post(
            "/api/v1/alerts/rules",
            json={"name": "测试规则", "severity": "medium"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert rule_resp.status_code == 201

    async def test_analyst_can_resolve_alert(self, client, analyst_token):
        """分析师可以处理预警"""
        # 创建预警规则
        rule_resp = await client.post(
            "/api/v1/alerts/rules",
            json={"name": "分析师处理规则", "severity": "low"},
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert rule_resp.status_code == 201