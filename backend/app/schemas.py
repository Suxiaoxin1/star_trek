"""Pydantic 数据校验模型"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ==================== 通用 ====================
class PaginatedResponse(BaseModel):
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# ==================== 竞品 ====================
class CompetitorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="竞品名称")
    name_en: str | None = Field(None, max_length=200)
    website: str | None = Field(None, max_length=500)
    logo_url: str | None = Field(None, max_length=1000)
    tier: str = Field("direct", pattern="^(direct|indirect|potential)$")
    description: str | None = None
    headquarters: str | None = None
    founded_year: int | None = None
    employee_count: str | None = None
    funding_stage: str | None = None
    total_funding: str | None = None
    tags: list[str] = []
    is_active: bool = True


class CompetitorCreate(CompetitorBase):
    pass


class CompetitorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    name_en: str | None = None
    website: str | None = None
    logo_url: str | None = None
    tier: str | None = Field(None, pattern="^(direct|indirect|potential)$")
    description: str | None = None
    headquarters: str | None = None
    founded_year: int | None = None
    employee_count: str | None = None
    funding_stage: str | None = None
    total_funding: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class CompetitorResponse(CompetitorBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    product_count: int = 0
    intel_count: int = 0

    class Config:
        from_attributes = True


# ==================== 产品 ====================
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    category: str | None = Field(None, max_length=100)
    description: str | None = None
    launch_date: datetime | None = None
    pricing_model: str | None = None
    target_market: str | None = None
    website: str | None = None
    tags: list[str] = []
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: UUID
    competitor_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 功能对比 ====================
class FeatureBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    feature_name: str = Field(..., min_length=1, max_length=300)
    support_level: str = Field("unknown", pattern="^(full|partial|none|unknown)$")
    description: str | None = None
    source_url: str | None = None


class FeatureCreate(FeatureBase):
    pass


class FeatureResponse(FeatureBase):
    id: UUID
    competitor_id: UUID
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 价格变动 ====================
class PricingHistoryBase(BaseModel):
    plan_name: str = Field(..., min_length=1, max_length=200)
    old_price: float | None = None
    new_price: float = Field(...)
    currency: str = "CNY"
    billing_cycle: str | None = None
    change_type: str | None = None
    change_description: str | None = None
    source_url: str | None = None
    detected_at: datetime


class PricingHistoryCreate(PricingHistoryBase):
    pass


class PricingHistoryResponse(PricingHistoryBase):
    id: UUID
    competitor_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 市场情报 ====================
class IntelligenceBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    summary: str | None = None
    category: str | None = Field(None, max_length=100)
    sentiment: str | None = Field(None, pattern="^(positive|neutral|negative)$")
    importance: int = Field(3, ge=1, le=5)
    source_url: str | None = None
    source_name: str | None = None
    published_at: datetime | None = None
    tags: list[str] = []


class IntelligenceCreate(IntelligenceBase):
    competitor_id: UUID


class IntelligenceResponse(IntelligenceBase):
    id: UUID
    competitor_id: UUID
    competitor_name: str = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 分析报告 ====================
class ReportBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str | None = None
    status: str = Field("draft", pattern="^(draft|in_progress|completed|archived)$")
    report_type: str | None = None
    tags: list[str] = []


class ReportCreate(ReportBase):
    intelligence_id: UUID | None = None


class ReportResponse(ReportBase):
    id: UUID
    intelligence_id: UUID | None = None
    generated_by: str = "manual"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 预警 ====================
class AlertRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    target_type: str | None = None
    keywords: list[str] = []
    severity: str = Field("medium", pattern="^(low|medium|high|critical)$")
    notification_channels: list[str] = ["email"]
    is_active: bool = True


class AlertRuleCreate(AlertRuleBase):
    target_id: UUID | None = None


class AlertRuleResponse(AlertRuleBase):
    id: UUID
    target_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    id: UUID
    rule_id: UUID
    rule_name: str = ""
    title: str
    content: str | None = None
    severity: str | None = None
    is_read: bool = False
    is_resolved: bool = False
    triggered_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
