"""通知服务单元测试 — SSE 推送 / 数据库通知 / 便捷方法

测试对象：app.services.notification.NotificationService（全局单例 notification_service）
为避免单例的 SSE 队列跨测试残留，每个测试使用唯一 user_id，并在结束后清理。
"""
import asyncio
from uuid import uuid4, UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AlertHistory
from app.services.notification import NotificationService, notification_service


@pytest.mark.asyncio
class TestSSEPush:
    """SSE 订阅与推送测试"""

    async def test_subscribe_creates_queue(self):
        """订阅后获得消息队列"""
        svc = NotificationService()
        user_id = f"user-{uuid4()}"
        try:
            queue = await svc.subscribe_sse(user_id)
            assert queue is not None
            assert queue.maxsize == 100
        finally:
            await svc.unsubscribe_sse(user_id)

    async def test_subscribe_reuses_existing_queue(self):
        """重复订阅返回同一队列"""
        svc = NotificationService()
        user_id = f"user-{uuid4()}"
        try:
            q1 = await svc.subscribe_sse(user_id)
            q2 = await svc.subscribe_sse(user_id)
            assert q1 is q2
        finally:
            await svc.unsubscribe_sse(user_id)

    async def test_push_sse_delivers_event(self):
        """推送事件到订阅者队列"""
        svc = NotificationService()
        user_id = f"user-{uuid4()}"
        try:
            queue = await svc.subscribe_sse(user_id)
            event = {"type": "test", "msg": "hello"}
            await svc.push_sse(user_id, event)
            received = queue.get_nowait()
            assert received == event
        finally:
            await svc.unsubscribe_sse(user_id)

    async def test_push_sse_to_nonexistent_user_noop(self):
        """向未订阅用户推送不报错"""
        svc = NotificationService()
        # 使用一个绝对不存在的 user_id
        await svc.push_sse(f"ghost-{uuid4()}", {"type": "noop"})

    async def test_push_sse_drops_when_queue_full(self):
        """队列满时丢弃新消息（不阻塞）"""
        svc = NotificationService()
        user_id = f"user-{uuid4()}"
        try:
            queue = await svc.subscribe_sse(user_id)
            # 填满队列（maxsize=100）
            for i in range(100):
                await svc.push_sse(user_id, {"i": i})
            assert queue.qsize() == 100
            # 第 101 条应被静默丢弃
            await svc.push_sse(user_id, {"i": 999})
            assert queue.qsize() == 100
        finally:
            await svc.unsubscribe_sse(user_id)

    async def test_unsubscribe_removes_queue(self):
        """取消订阅后队列被移除"""
        svc = NotificationService()
        user_id = f"user-{uuid4()}"
        await svc.subscribe_sse(user_id)
        await svc.unsubscribe_sse(user_id)
        # 取消后再推送不应抛错，且不应有残留队列
        await svc.push_sse(user_id, {"type": "after_unsub"})
        assert user_id not in svc._sse_clients


@pytest.mark.asyncio
class TestDBNotification:
    """数据库通知记录测试"""

    async def test_create_db_notification(self, db_session: AsyncSession):
        """创建数据库通知记录"""
        svc = NotificationService()
        alert = await svc.create_db_notification(
            db_session,
            title="测试通知",
            content="这是一条测试通知",
            severity="high",
            source="unit_test",
        )
        assert alert.id is not None
        assert alert.title == "测试通知"
        assert alert.content == "这是一条测试通知"
        assert alert.severity == "high"
        assert alert.triggered_by == "unit_test"
        assert alert.triggered_at is not None

    async def test_create_db_notification_defaults(self, db_session: AsyncSession):
        """使用默认参数创建通知"""
        svc = NotificationService()
        alert = await svc.create_db_notification(db_session, title="默认通知")
        assert alert.severity == "medium"
        assert alert.triggered_by == "ai_analysis"


@pytest.mark.asyncio
class TestConvenienceMethods:
    """便捷通知方法测试"""

    async def test_notify_analysis_complete(self, db_session: AsyncSession):
        """分析完成通知"""
        svc = NotificationService()
        user_id = uuid4()
        report_id = uuid4()
        try:
            await svc.notify_analysis_complete(
                db_session,
                user_id=user_id,
                report_id=report_id,
                title="Q2 竞品报告",
                severity="info",
            )
            # 验证数据库通知已创建
            from sqlalchemy import select
            result = (await db_session.execute(
                select(AlertHistory).where(AlertHistory.title == "分析完成: Q2 竞品报告")
            )).scalars().first()
            assert result is not None
            assert str(report_id) in result.content
        finally:
            await svc.unsubscribe_sse(str(user_id))

    async def test_notify_analysis_error(self, db_session: AsyncSession):
        """分析失败通知"""
        svc = NotificationService()
        user_id = uuid4()
        try:
            await svc.notify_analysis_error(
                db_session,
                user_id=user_id,
                error="LLM 调用超时",
                severity="high",
            )
            from sqlalchemy import select
            result = (await db_session.execute(
                select(AlertHistory).where(AlertHistory.title == "分析任务失败")
            )).scalars().first()
            assert result is not None
            assert "LLM 调用超时" in result.content
            assert result.severity == "high"
        finally:
            await svc.unsubscribe_sse(str(user_id))

    async def test_notify_analysis_complete_pushes_sse(self, db_session: AsyncSession):
        """分析完成通知同时推送 SSE 事件"""
        svc = NotificationService()
        user_id = uuid4()
        report_id = uuid4()
        try:
            queue = await svc.subscribe_sse(str(user_id))
            await svc.notify_analysis_complete(
                db_session,
                user_id=user_id,
                report_id=report_id,
                title="SSE 报告",
            )
            event = queue.get_nowait()
            assert event["type"] == "analysis_complete"
            assert event["report_id"] == str(report_id)
            assert event["title"] == "SSE 报告"
        finally:
            await svc.unsubscribe_sse(str(user_id))

    async def test_notify_analysis_error_pushes_sse(self, db_session: AsyncSession):
        """分析失败通知同时推送 SSE 事件"""
        svc = NotificationService()
        user_id = uuid4()
        try:
            queue = await svc.subscribe_sse(str(user_id))
            await svc.notify_analysis_error(
                db_session,
                user_id=user_id,
                error="内部错误",
            )
            event = queue.get_nowait()
            assert event["type"] == "analysis_error"
            assert "内部错误" in event["error"]
        finally:
            await svc.unsubscribe_sse(str(user_id))


@pytest.mark.asyncio
class TestWebsocketStub:
    """WebSocket 预留接口测试"""

    async def test_push_websocket_noop(self):
        """WebSocket 推送为预留实现，不应抛错"""
        svc = NotificationService()
        # 当前为空实现，调用应直接返回 None
        result = await svc.push_websocket("any-user", {"type": "test"})
        assert result is None


def test_global_singleton_exists():
    """全局单例已实例化"""
    assert notification_service is not None
    assert isinstance(notification_service, NotificationService)
