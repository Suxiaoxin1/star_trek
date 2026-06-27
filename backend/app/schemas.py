"""Pydantic 数据校验模型"""
from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict


def _naivify_dt(v: datetime) -> datetime:
    """将时区感知的 datetime 转为 naive UTC，避免 PostgreSQL TIMESTAMP WITHOUT TIME ZONE 报错"""
    if isinstance(v, datetime) and v.tzinfo is not None:
        return v.astimezone(timezone.utc).replace(tzinfo=None)
    return v


# ==================== 通用 ====================
class PaginatedResponse(BaseModel):
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# ==================== 竞品 ====================
class CompetitorBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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
    metadata: dict = Field(default={}, alias="metadata_", description="扩展元数据（LLM 技术参数等）")
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
    metadata: dict | None = None
    is_active: bool | None = None


class CompetitorResponse(CompetitorBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    product_count: int = 0
    intel_count: int = 0

    class Config:
        from_attributes = True
        populate_by_name = True


# ==================== 产品 ====================
class ProductBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=300)
    category: str | None = Field(None, max_length=100)
    description: str | None = None
    launch_date: datetime | None = None
    pricing_model: str | None = None
    target_market: str | None = None
    website: str | None = None
    tags: list[str] = []
    metadata: dict = Field(default={}, alias="metadata_", description="扩展元数据")
    is_active: bool = True

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: dict) -> dict:
        """将空字符串转为 None，兼容前端表单提交"""
        if isinstance(data, dict):
            for key in ("category", "description", "launch_date", "pricing_model", "target_market", "website"):
                if data.get(key) == "" or data.get(key) is None:
                    data[key] = None
        return data

    @field_validator("launch_date", mode="after")
    @classmethod
    def naivify_launch_date(cls, v: datetime | None) -> datetime | None:
        """将时区感知的 datetime 转为 naive，兼容前端 Date 对象序列化"""
        if v is None:
            return None
        return _naivify_dt(v)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=300)
    category: str | None = None
    description: str | None = None
    launch_date: datetime | None = None
    pricing_model: str | None = None
    target_market: str | None = None
    website: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    id: UUID
    competitor_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ==================== 功能对比 ====================
class FeatureBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    feature_name: str = Field(..., min_length=1, max_length=300)
    support_level: str = Field("unknown", pattern="^(full|partial|none|unknown)$")
    description: str | None = None
    source_url: str | None = None

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: dict) -> dict:
        if isinstance(data, dict):
            for key in ("description", "source_url"):
                if data.get(key) == "":
                    data[key] = None
        return data


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

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: dict) -> dict:
        """将空字符串转为 None，兼容前端表单提交"""
        if isinstance(data, dict):
            for key in ("billing_cycle", "change_type", "change_description", "source_url"):
                if data.get(key) == "":
                    data[key] = None
        return data

    @field_validator("detected_at", mode="after")
    @classmethod
    def naivify_detected_at(cls, v: datetime) -> datetime:
        """将时区感知的 datetime 转为 naive，兼容前端 ISO 字符串"""
        return _naivify_dt(v)


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

    @model_validator(mode="before")
    @classmethod
    def empty_str_to_none(cls, data: dict) -> dict:
        if isinstance(data, dict):
            for key in ("summary", "category", "source_url", "source_name", "published_at"):
                if data.get(key) == "" or data.get(key) is None:
                    data[key] = None
        return data

    @field_validator("sentiment", mode="before")
    @classmethod
    def none_if_empty_sentiment(cls, v: object) -> object:
        """将空字符串转为 None，避免 pattern 校验失败"""
        return None if v == "" else v

    @field_validator("published_at", mode="after")
    @classmethod
    def naivify_published_at(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        return _naivify_dt(v)


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


# ==================== 认证 ====================
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, description="用户名")
    email: str = Field(..., max_length=320, description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    display_name: str | None = Field(None, max_length=200, description="显示名称")
    role: str = Field("viewer", pattern="^(admin|analyst|viewer)$", description="角色")


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    display_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ==================== 数据源 ====================
class DataSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300, description="数据源名称")
    source_type: str = Field(..., pattern="^(rss|api|web_scraper|social_media|news|manual)$", description="数据源类型")
    url: str | None = Field(None, max_length=1000)
    crawl_config: dict = {}
    api_config: dict = {}
    is_active: bool = True
    crawl_interval_minutes: int = Field(360, ge=10, description="采集间隔（分钟）")


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=300)
    source_type: str | None = Field(None, pattern="^(rss|api|web_scraper|social_media|news|manual)$")
    url: str | None = None
    crawl_config: dict | None = None
    api_config: dict | None = None
    is_active: bool | None = None
    crawl_interval_minutes: int | None = Field(None, ge=10)


class DataSourceResponse(DataSourceBase):
    id: UUID
    last_crawled_at: datetime | None = None
    last_status: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 采集数据 ====================
class CollectedDataResponse(BaseModel):
    id: UUID
    source_id: UUID | None = None
    source_name: str = ""
    title: str | None = None
    content: str | None = None
    content_hash: str | None = None
    url: str | None = None
    language: str = "zh"
    raw_data: dict = {}
    collected_at: datetime
    processed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== AI 智能分析 ====================
class AISentimentRequest(BaseModel):
    """情感分析请求"""
    text: str | None = Field(None, min_length=1, max_length=10000, description="待分析文本")
    texts: list[str] | None = Field(None, description="批量分析文本列表")
    model: str | None = Field(None, description="指定 LLM 模型（默认使用配置模型）")


class AISentimentResponse(BaseModel):
    """情感分析响应"""
    sentiment: str = "neutral"
    sentiment_score: float = 0.5
    confidence: float = 0.0
    key_phrases: list[str] = []
    reasoning: str = ""


class AISummaryRequest(BaseModel):
    """摘要提取请求"""
    text: str = Field(..., min_length=1, max_length=50000, description="待提取摘要的文本")
    model: str | None = Field(None, description="指定 LLM 模型")


class AISummaryResponse(BaseModel):
    """摘要提取响应"""
    summary: str = ""
    key_points: list[str] = []
    impact_level: str = "medium"
    affected_areas: list[str] = []
    action_items: list[str] = []


class AIReportRequest(BaseModel):
    """AI 生成报告请求"""
    title: str | None = Field(None, max_length=500, description="报告标题（可选，自动生成）")
    competitor_id: str | None = Field(None, description="竞品 ID（用于获取关联情报）")
    intelligence_ids: list[str] | None = Field(None, description="指定情报 ID 列表")
    intelligence_limit: int | None = Field(20, ge=1, le=100, description="最大情报数量")
    report_type: str | None = Field("competitor_analysis", description="报告类型")
    model: str | None = Field(None, description="指定 LLM 模型")
    tags: list[str] | None = Field(None, description="标签")


class AICompetitorRequest(BaseModel):
    """竞品深度分析请求"""
    competitor_id: str = Field(..., description="竞品 ID")
    intelligence_limit: int | None = Field(20, ge=1, le=100, description="最大情报数量")
    model: str | None = Field(None, description="指定 LLM 模型")


class AICompetitorResponse(BaseModel):
    """竞品深度分析响应"""
    competitor_id: str
    competitor_name: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    market_position: str = ""
    threat_level: str = "medium"
    opportunity_for_us: list[str] = []
    strategic_recommendations: list[str] = []
    recent_highlights: list[str] = []
    risk_factors: list[str] = []


class AIStatusResponse(BaseModel):
    """AI 服务状态"""
    available: bool
    model: str | None = None
    api_base: str = ""
    message: str = ""
