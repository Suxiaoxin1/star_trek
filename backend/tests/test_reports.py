"""分析报告 API 测试 — CRUD / 关联校验 / 权限校验"""
import pytest

from tests.conftest import auth_headers


# 测试用例创建报告的辅助函数
async def _create_report(client, token, title="测试报告", **kwargs):
    """创建一条分析报告，返回响应数据"""
    payload = {"title": title, "status": "draft", "report_type": "competitor_analysis"}
    payload.update(kwargs)
    resp = await client.post(
        "/api/v1/reports/",
        json=payload,
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
class TestReportsCRUD:
    """分析报告增删改查测试"""

    async def test_create_report_as_analyst(self, client, analyst_token):
        """分析师创建报告"""
        data = await _create_report(client, analyst_token, "Q1 竞品分析报告")
        assert data["title"] == "Q1 竞品分析报告"
        assert data["status"] == "draft"
        assert data["report_type"] == "competitor_analysis"
        assert data["generated_by"] == "manual"

    async def test_create_report_as_viewer_forbidden(self, client, viewer_token):
        """观察者不能创建报告"""
        resp = await client.post(
            "/api/v1/reports/",
            json={"title": "不应创建"},
            headers=auth_headers(viewer_token),
        )
        assert resp.status_code == 403

    async def test_create_report_with_invalid_status(self, client, analyst_token):
        """非法 status 字段被 schema 拒绝"""
        resp = await client.post(
            "/api/v1/reports/",
            json={"title": "非法状态", "status": "invalid_status"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 422

    async def test_create_report_with_nonexistent_intelligence(self, client, analyst_token):
        """关联不存在的情报时返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.post(
            "/api/v1/reports/",
            json={"title": "关联情报报告", "intelligence_id": fake_id},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 404
        assert "情报不存在" in resp.json()["detail"]

    async def test_list_reports(self, client, admin_token, analyst_token):
        """获取报告列表"""
        await _create_report(client, analyst_token, "列表报告1")
        await _create_report(client, analyst_token, "列表报告2")

        resp = await client.get("/api/v1/reports/", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    async def test_list_reports_filter_by_status(self, client, admin_token, analyst_token):
        """按状态筛选报告"""
        await _create_report(client, analyst_token, "状态筛选报告", status="completed")

        resp = await client.get(
            "/api/v1/reports/?status=completed",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["status"] == "completed" for i in items)

    async def test_list_reports_filter_by_type(self, client, admin_token, analyst_token):
        """按报告类型筛选"""
        await _create_report(client, analyst_token, "类型筛选报告", report_type="swot")

        resp = await client.get(
            "/api/v1/reports/?report_type=swot",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["report_type"] == "swot" for i in items)

    async def test_get_report_detail(self, client, admin_token, analyst_token):
        """获取报告详情"""
        created = await _create_report(client, analyst_token, "详情报告")

        resp = await client.get(
            f"/api/v1/reports/{created['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "详情报告"

    async def test_get_nonexistent_report(self, client, admin_token):
        """获取不存在的报告返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/reports/{fake_id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 404

    async def test_update_report(self, client, analyst_token):
        """更新报告内容与状态"""
        created = await _create_report(client, analyst_token, "待更新报告")

        resp = await client.put(
            f"/api/v1/reports/{created['id']}",
            json={"title": "已更新报告", "status": "completed", "content": "# 正文"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "已更新报告"
        assert data["status"] == "completed"
        assert data["content"] == "# 正文"

    async def test_update_nonexistent_report(self, client, analyst_token):
        """更新不存在的报告返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.put(
            f"/api/v1/reports/{fake_id}",
            json={"title": "x"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 404

    async def test_delete_report_as_admin(self, client, admin_token, analyst_token):
        """管理员删除报告"""
        created = await _create_report(client, analyst_token, "待删除报告")

        resp = await client.delete(
            f"/api/v1/reports/{created['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert "已删除" in resp.json()["detail"]

    async def test_delete_report_as_analyst_forbidden(self, client, analyst_token):
        """分析师不能删除报告"""
        created = await _create_report(client, analyst_token, "分析师不能删")

        resp = await client.delete(
            f"/api/v1/reports/{created['id']}",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestReportsPermission:
    """报告接口权限测试"""

    async def test_no_token_list_forbidden(self, client):
        """无 token 访问报告列表"""
        resp = await client.get("/api/v1/reports/")
        assert resp.status_code == 401

    async def test_no_token_create_forbidden(self, client):
        """无 token 创建报告"""
        resp = await client.post(
            "/api/v1/reports/",
            json={"title": "x"},
        )
        assert resp.status_code == 401
