"""预警管理 API 测试 — 规则 CRUD / 历史 / 标记 / 统计 / 权限

注：预警历史 AlertHistory 必须关联 AlertRule，而路由未暴露创建历史的接口，
因此通过直接操作数据库（db_session）构造测试数据。
"""
from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AlertRule, AlertHistory
from tests.conftest import auth_headers


# 创建预警规则的辅助函数
async def _create_rule(client, token, name="测试规则", **kwargs):
    """创建一条预警规则，返回响应数据"""
    payload = {
        "name": name,
        "severity": "medium",
        "keywords": ["融资", "新品"],
        "notification_channels": ["email"],
        "is_active": True,
    }
    payload.update(kwargs)
    resp = await client.post(
        "/api/v1/alerts/rules",
        json=payload,
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.json()


# 通过数据库直接创建预警历史的辅助函数
async def _create_alert_history(db_session: AsyncSession, rule_id, title="触发预警", severity="high"):
    """直接向数据库插入一条预警历史记录

    rule_id 来自 API JSON 响应（字符串），需转为 UUID 对象以匹配模型字段类型。
    """
    # 字符串 ID 转为 UUID 对象（API 返回的 JSON 中 id 是字符串）
    rule_uuid = UUID(rule_id) if isinstance(rule_id, str) else rule_id
    alert = AlertHistory(
        rule_id=rule_uuid,
        title=title,
        content="自动触发的预警内容",
        severity=severity,
        triggered_by="test_source",
        is_read=False,
        is_resolved=False,
        triggered_at=datetime.utcnow(),
    )
    db_session.add(alert)
    await db_session.flush()
    await db_session.refresh(alert)
    return alert


@pytest.mark.asyncio
class TestAlertRules:
    """预警规则 CRUD 测试"""

    async def test_create_rule_as_analyst(self, client, analyst_token):
        """分析师创建预警规则"""
        data = await _create_rule(client, analyst_token, "价格监控规则")
        assert data["name"] == "价格监控规则"
        assert data["severity"] == "medium"
        assert data["keywords"] == ["融资", "新品"]
        assert data["is_active"] is True

    async def test_create_rule_as_viewer_forbidden(self, client, viewer_token):
        """观察者不能创建规则"""
        resp = await client.post(
            "/api/v1/alerts/rules",
            json={"name": "不应创建"},
            headers=auth_headers(viewer_token),
        )
        assert resp.status_code == 403

    async def test_create_rule_with_invalid_severity(self, client, analyst_token):
        """非法 severity 字段被 schema 拒绝"""
        resp = await client.post(
            "/api/v1/alerts/rules",
            json={"name": "非法严重度", "severity": "extreme"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 422

    async def test_list_rules(self, client, admin_token, analyst_token):
        """获取规则列表"""
        await _create_rule(client, analyst_token, "列表规则1")
        await _create_rule(client, analyst_token, "列表规则2")

        resp = await client.get("/api/v1/alerts/rules", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2

    async def test_list_rules_filter_by_active(self, client, admin_token, analyst_token):
        """按启用状态筛选规则"""
        await _create_rule(client, analyst_token, "启用规则", is_active=True)
        await _create_rule(client, analyst_token, "停用规则", is_active=False)

        resp = await client.get(
            "/api/v1/alerts/rules?is_active=true",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["is_active"] is True for i in items)

    async def test_update_rule(self, client, analyst_token):
        """更新预警规则"""
        created = await _create_rule(client, analyst_token, "待更新规则")

        resp = await client.put(
            f"/api/v1/alerts/rules/{created['id']}",
            json={"name": "已更新规则", "severity": "critical"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "已更新规则"
        assert data["severity"] == "critical"

    async def test_update_nonexistent_rule(self, client, analyst_token):
        """更新不存在的规则返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.put(
            f"/api/v1/alerts/rules/{fake_id}",
            json={"name": "x"},
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 404

    async def test_delete_rule_as_admin(self, client, admin_token, analyst_token):
        """管理员删除规则"""
        created = await _create_rule(client, analyst_token, "待删除规则")

        resp = await client.delete(
            f"/api/v1/alerts/rules/{created['id']}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert "已删除" in resp.json()["detail"]

    async def test_delete_rule_as_analyst_forbidden(self, client, analyst_token):
        """分析师不能删除规则"""
        created = await _create_rule(client, analyst_token, "分析师不能删")

        resp = await client.delete(
            f"/api/v1/alerts/rules/{created['id']}",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestAlertHistory:
    """预警历史记录测试"""

    async def test_list_history_empty(self, client, admin_token):
        """空库时历史列表为空"""
        resp = await client.get("/api/v1/alerts/history", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_history_with_data(self, client, admin_token, analyst_token, db_session):
        """查询历史记录（带规则名）"""
        rule = await _create_rule(client, analyst_token, "历史关联规则")
        await _create_alert_history(db_session, rule["id"], "历史预警1", "high")
        await _create_alert_history(db_session, rule["id"], "历史预警2", "low")

        resp = await client.get("/api/v1/alerts/history", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        # 验证返回的规则名
        assert any(i["rule_name"] == "历史关联规则" for i in data["items"])

    async def test_list_history_filter_by_severity(self, client, admin_token, analyst_token, db_session):
        """按严重程度筛选历史"""
        rule = await _create_rule(client, analyst_token, "严重度筛选规则")
        await _create_alert_history(db_session, rule["id"], "高级预警", "high")
        await _create_alert_history(db_session, rule["id"], "低级预警", "low")

        resp = await client.get(
            "/api/v1/alerts/history?severity=high",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all(i["severity"] == "high" for i in items)

    async def test_mark_alert_read(self, client, admin_token, analyst_token, db_session):
        """标记预警为已读"""
        rule = await _create_rule(client, analyst_token, "已读规则")
        alert = await _create_alert_history(db_session, rule["id"], "待标记预警")

        resp = await client.put(
            f"/api/v1/alerts/history/{alert.id}/read",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert "已标记" in resp.json()["detail"]

    async def test_mark_nonexistent_alert_read(self, client, admin_token):
        """标记不存在的预警返回 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.put(
            f"/api/v1/alerts/history/{fake_id}/read",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 404

    async def test_resolve_alert_as_analyst(self, client, analyst_token, db_session):
        """分析师标记预警为已处理"""
        rule = await _create_rule(client, analyst_token, "处理规则")
        alert = await _create_alert_history(db_session, rule["id"], "待处理预警")

        resp = await client.put(
            f"/api/v1/alerts/history/{alert.id}/resolve",
            headers=auth_headers(analyst_token),
        )
        assert resp.status_code == 200
        assert "已处理" in resp.json()["detail"]

    async def test_resolve_alert_as_viewer_forbidden(self, client, viewer_token, analyst_token, db_session):
        """观察者不能标记已处理"""
        rule = await _create_rule(client, analyst_token, "权限规则")
        alert = await _create_alert_history(db_session, rule["id"], "观察者不能处理")

        resp = await client.put(
            f"/api/v1/alerts/history/{alert.id}/resolve",
            headers=auth_headers(viewer_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestAlertStats:
    """预警统计接口测试"""

    async def test_stats_empty(self, client, admin_token):
        """空库时统计返回零值"""
        resp = await client.get("/api/v1/alerts/stats", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["unread_alerts"] == 0
        assert data["unresolved_alerts"] == 0
        assert data["active_rules"] == 0

    async def test_stats_with_data(self, client, admin_token, analyst_token, db_session):
        """有数据时统计正确"""
        rule = await _create_rule(client, analyst_token, "统计规则", is_active=True)
        await _create_alert_history(db_session, rule["id"], "统计预警1", "high")
        await _create_alert_history(db_session, rule["id"], "统计预警2", "medium")

        resp = await client.get("/api/v1/alerts/stats", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["unread_alerts"] >= 2
        assert data["unresolved_alerts"] >= 2
        assert data["active_rules"] >= 1


@pytest.mark.asyncio
class TestAlertsPermission:
    """预警接口权限测试"""

    async def test_no_token_list_rules_forbidden(self, client):
        """无 token 访问规则列表"""
        resp = await client.get("/api/v1/alerts/rules")
        assert resp.status_code == 401

    async def test_no_token_list_history_forbidden(self, client):
        """无 token 访问历史列表"""
        resp = await client.get("/api/v1/alerts/history")
        assert resp.status_code == 401

    async def test_no_token_stats_forbidden(self, client):
        """无 token 访问统计"""
        resp = await client.get("/api/v1/alerts/stats")
        assert resp.status_code == 401
