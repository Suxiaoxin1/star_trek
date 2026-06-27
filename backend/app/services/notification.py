"""通知推送服务 — 统一通知渠道

支持的渠道：
  - database: 数据库记录（始终启用）
  - sse: Server-Sent Events 推送
  - websocket: WebSocket 推送（预留接口）
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AlertHistory


class NotificationService:
    """统一通知服务"""

    def __init__(self):
        self._sse_clients: dict[str, asyncio.Queue] = {}  # user_id -> queue
        self._lock = asyncio.Lock()

    # ================================================================
    #  数据库通知
    # ================================================================

    async def create_db_notification(
        self,
        db: AsyncSession,
        *,
        title: str,
        content: str = "",
        severity: str = "medium",
        target_user_id: UUID | None = None,
        source: str = "ai_analysis",
    ) -> AlertHistory:
        """创建数据库通知记录"""
        alert = AlertHistory(
            title=title,
            content=content,
            severity=severity,
            triggered_by=source,
            triggered_at=datetime.now(timezone.utc),
        )
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        return alert

    # ================================================================
    #  SSE 推送
    # ================================================================

    async def subscribe_sse(self, user_id: str) -> asyncio.Queue:
        """订阅 SSE 推送"""
        async with self._lock:
            if user_id not in self._sse_clients:
                self._sse_clients[user_id] = asyncio.Queue(maxsize=100)
            return self._sse_clients[user_id]

    async def push_sse(self, user_id: str, event: dict[str, Any]) -> None:
        """向指定用户推送 SSE 事件"""
        async with self._lock:
            queue = self._sse_clients.get(user_id)
        if queue:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # 丢弃旧消息

    async def unsubscribe_sse(self, user_id: str) -> None:
        """取消订阅"""
        async with self._lock:
            self._sse_clients.pop(user_id, None)

    # ================================================================
    #  WebSocket 推送（预留）
    # ================================================================

    async def push_websocket(self, user_id: str, message: dict[str, Any]) -> None:
        """向指定用户推送 WebSocket 消息（预留实现）"""
        # TODO: 集成 WebSocket manager
        pass

    # ================================================================
    #  便捷方法
    # ================================================================

    async def notify_analysis_complete(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        report_id: UUID,
        title: str,
        severity: str = "info",
    ) -> None:
        """通知：分析任务完成"""
        await self.create_db_notification(
            db,
            title=f"分析完成: {title}",
            content=f"报告 {report_id} 已成功生成",
            severity=severity,
            source="ai_analysis",
        )
        await self.push_sse(str(user_id), {
            "type": "analysis_complete",
            "report_id": str(report_id),
            "title": title,
        })

    async def notify_analysis_error(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        error: str,
        severity: str = "high",
    ) -> None:
        """通知：分析任务出错"""
        await self.create_db_notification(
            db,
            title="分析任务失败",
            content=error,
            severity=severity,
            source="ai_analysis",
        )
        await self.push_sse(str(user_id), {
            "type": "analysis_error",
            "error": error,
        })


# 全局单例
notification_service = NotificationService()
