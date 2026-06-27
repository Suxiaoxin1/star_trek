"""AI 相关扩展 Schemas — 模型列表、任务状态、用量统计"""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ModelInfoSchema(BaseModel):
    """单个可用模型信息"""
    id: str
    provider: str
    model_id: str
    base_url: str
    max_tokens: int
    context_window: int
    is_default: bool = False
    status: str = "active"

    class Config:
        from_attributes = True


class ModelsListResponse(BaseModel):
    """可用模型列表响应"""
    models: list[ModelInfoSchema]
    total: int


class TaskStatusSchema(BaseModel):
    """Celery 异步任务状态"""
    task_id: str
    status: str  # pending / running / success / failure / revoked
    progress: int = 0  # 0-100
    current_step: str = ""
    total_steps: int = 0
    result: dict | None = None
    error: str | None = None
    created_at: datetime | None = None
    finished_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """任务状态查询响应"""
    success: bool
    task: TaskStatusSchema | None = None


class TokenUsageByProvider(BaseModel):
    """按提供商分组的用量统计"""
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class UsageStatsSchema(BaseModel):
    """Token 用量统计"""
    period: str
    call_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    by_provider: dict[str, TokenUsageByProvider] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class UsageStatsResponse(BaseModel):
    """用量统计响应"""
    success: bool
    stats: UsageStatsSchema | None = None
