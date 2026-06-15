"""数据库模型 —— 核心实体

Schema 设计说明：
  竞品分析核心流程：数据源 → 竞品 → 产品/功能 → 市场情报 → 分析报告

  ER 关系概览：
    Competitor  1──N  Product
    Competitor  1──N  CompetitorFeature
    Competitor  1──N  PricingHistory
    DataSource  1──N  CollectedData
    Competitor  1──N  MarketIntelligence
    MarketIntelligence  1──N  AnalysisReport
    Competitor  1──N  SentimentData
    AlertRule   1──N  AlertHistory
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    DateTime, ForeignKey, Enum as SAEnum, JSON, BigInteger, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


# ======================= 枚举类型 =======================
class CompetitorTier(str, SAEnum):
    DIRECT = "direct"         # 直接竞品
    INDIRECT = "indirect"     # 间接竞品
    POTENTIAL = "potential"   # 潜在竞品


class DataSourceType(str, SAEnum):
    RSS = "rss"
    API = "api"
    WEB_SCRAPER = "web_scraper"
    SOCIAL_MEDIA = "social_media"
    NEWS = "news"
    MANUAL = "manual"


class AnalysisStatus(str, SAEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AlertSeverity(str, SAEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ======================= 1. 竞品 =======================
class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True, comment="竞品名称")
    name_en = Column(String(200), comment="英文名称")
    website = Column(String(500), comment="官网地址")
    logo_url = Column(String(1000), comment="Logo 地址")
    tier = Column(
        SAEnum(CompetitorTier),
        default=CompetitorTier.DIRECT,
        index=True,
        comment="竞品层级",
    )
    description = Column(Text, comment="竞品描述")
    headquarters = Column(String(200), comment="总部所在地")
    founded_year = Column(Integer, comment="成立年份")
    employee_count = Column(String(50), comment="员工规模")
    funding_stage = Column(String(100), comment="融资阶段")
    total_funding = Column(String(100), comment="融资总额")
    tags = Column(JSON, default=list, comment="标签列表")
    metadata_ = Column("metadata", JSON, default=dict, comment="扩展元数据")

    is_active = Column(Boolean, default=True, index=True, comment="是否活跃")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联
    products = relationship("Product", back_populates="competitor", cascade="all, delete-orphan")
    features = relationship("CompetitorFeature", back_populates="competitor", cascade="all, delete-orphan")
    pricing_history = relationship("PricingHistory", back_populates="competitor", cascade="all, delete-orphan")
    intelligence = relationship("MarketIntelligence", back_populates="competitor", cascade="all, delete-orphan")
    sentiment_data = relationship("SentimentData", back_populates="competitor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Competitor {self.name}>"


# ======================= 2. 竞品产品/服务 =======================
class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(300), nullable=False, comment="产品名称")
    category = Column(String(100), index=True, comment="产品分类")
    description = Column(Text, comment="产品描述")
    launch_date = Column(DateTime, comment="上线时间")
    pricing_model = Column(String(200), comment="定价模式（免费/订阅/一次性）")
    target_market = Column(String(300), comment="目标市场")
    website = Column(String(500), comment="产品页面")
    tags = Column(JSON, default=list, comment="标签")
    metadata_ = Column("metadata", JSON, default=dict)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="products")

    def __repr__(self):
        return f"<Product {self.name}>"


# ======================= 3. 竞品功能对比 =======================
class CompetitorFeature(Base):
    """可扩展的功能对比矩阵: 每个竞品的每个功能点一行"""
    __tablename__ = "competitor_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(String(100), nullable=False, index=True, comment="功能大类（如 AI/数据分析/协作）")
    feature_name = Column(String(300), nullable=False, index=True, comment="功能名称")
    support_level = Column(
        String(20), default="unknown",
        comment="支持程度: full / partial / none / unknown",
    )
    description = Column(Text, comment="功能详情")
    source_url = Column(String(1000), comment="信息来源链接")
    verified_at = Column(DateTime, comment="核验时间")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="features")

    __table_args__ = (
        Index("ix_feature_competitor_name", "competitor_id", "feature_name"),
    )

    def __repr__(self):
        return f"<Feature {self.category}/{self.feature_name}: {self.support_level}>"


# ======================= 4. 价格变动历史 =======================
class PricingHistory(Base):
    __tablename__ = "pricing_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_name = Column(String(200), nullable=False, comment="套餐名称")
    old_price = Column(Float, comment="旧价格")
    new_price = Column(Float, nullable=False, comment="新价格")
    currency = Column(String(10), default="CNY", comment="币种")
    billing_cycle = Column(String(20), comment="计费周期: monthly/yearly")
    change_type = Column(String(20), comment="变动类型: increase/decrease/new_plan/removed")
    change_description = Column(Text, comment="变动说明")
    source_url = Column(String(1000), comment="信息来源")
    detected_at = Column(DateTime, nullable=False, index=True, comment="检测时间")

    created_at = Column(DateTime, default=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="pricing_history")

    def __repr__(self):
        return f"<Pricing {self.competitor_id} {self.plan_name}: {self.old_price}→{self.new_price}>"


# ======================= 5. 数据源 =======================
class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False, comment="数据源名称")
    source_type = Column(
        SAEnum(DataSourceType),
        nullable=False,
        index=True,
        comment="数据源类型",
    )
    url = Column(String(1000), comment="数据源 URL")
    crawl_config = Column(JSON, default=dict, comment="爬虫配置（选择器、频率等）")
    api_config = Column(JSON, default=dict, comment="API 配置（endpoint, headers, auth）")

    is_active = Column(Boolean, default=True, comment="是否启用")
    crawl_interval_minutes = Column(Integer, default=360, comment="采集间隔（分钟）")
    last_crawled_at = Column(DateTime, comment="上次采集时间")
    last_status = Column(String(20), comment="上次采集状态: success/failed")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    collected_data = relationship("CollectedData", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DataSource {self.name} [{self.source_type}]>"


# ======================= 6. 采集数据（原始） =======================
class CollectedData(Base):
    __tablename__ = "collected_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(500), comment="标题")
    content = Column(Text, comment="原始内容")
    content_hash = Column(String(64), index=True, comment="内容 SHA256 哈希（去重）")
    url = Column(String(2000), comment="原始链接")
    language = Column(String(10), default="zh", comment="语言")
    raw_data = Column(JSON, default=dict, comment="原始结构化数据")
    collected_at = Column(DateTime, nullable=False, index=True, comment="采集时间")
    processed = Column(Boolean, default=False, index=True, comment="是否已处理")

    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("DataSource", back_populates="collected_data")

    __table_args__ = (
        Index("ix_collected_source_hash", "source_id", "content_hash"),
    )

    def __repr__(self):
        return f"<CollectedData {self.title[:50]}>"


# ======================= 7. 市场情报 =======================
class MarketIntelligence(Base):
    __tablename__ = "market_intelligence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False, comment="情报标题")
    summary = Column(Text, comment="情报摘要")
    category = Column(String(100), index=True, comment="分类: product_update/funding/partnership/hr/policy")
    sentiment = Column(String(20), index=True, comment="情感: positive/neutral/negative")
    importance = Column(Integer, default=3, comment="重要度 1-5")
    source_url = Column(String(2000), comment="来源链接")
    source_name = Column(String(300), comment="来源名称")
    published_at = Column(DateTime, index=True, comment="情报发布日期")
    tags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="intelligence")
    reports = relationship("AnalysisReport", back_populates="intelligence", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Intel {self.category}: {self.title[:50]}>"


# ======================= 8. 分析报告 =======================
class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intelligence_id = Column(
        UUID(as_uuid=True),
        ForeignKey("market_intelligence.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title = Column(String(500), nullable=False, comment="报告标题")
    content = Column(Text, comment="报告正文（Markdown）")
    status = Column(
        SAEnum(AnalysisStatus),
        default=AnalysisStatus.DRAFT,
        index=True,
        comment="状态",
    )
    report_type = Column(String(100), index=True, comment="报告类型: competitor_analysis/swot/trend/alert")
    generated_by = Column(String(50), default="manual", comment="生成方式: manual/ai/scheduled")
    ai_model = Column(String(100), comment="AI 模型名称")
    ai_prompt = Column(Text, comment="AI Prompt（用于追溯）")
    tags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intelligence = relationship("MarketIntelligence", back_populates="reports")

    def __repr__(self):
        return f"<Report {self.report_type}: {self.title[:50]}>"


# ======================= 9. 舆情/用户反馈 =======================
class SentimentData(Base):
    __tablename__ = "sentiment_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform = Column(String(100), index=True, comment="平台: twitter/weibo/reddit/app_store")
    content = Column(Text, nullable=False, comment="原始内容")
    author = Column(String(200), comment="作者")
    sentiment = Column(String(20), index=True, comment="情感: positive/neutral/negative")
    sentiment_score = Column(Float, comment="情感分数 0-1")
    engagement_count = Column(Integer, default=0, comment="互动量")
    published_at = Column(DateTime, index=True, comment="发布时间")
    source_url = Column(String(2000), comment="来源链接")

    created_at = Column(DateTime, default=datetime.utcnow)

    competitor = relationship("Competitor", back_populates="sentiment_data")

    def __repr__(self):
        return f"<Sentiment {self.platform}: {self.sentiment}>"


# ======================= 10. 预警规则 =======================
class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")
    target_type = Column(String(50), comment="监控对象: competitor/product/keyword")
    target_id = Column(UUID(as_uuid=True), nullable=True, comment="监控对象 ID")
    keywords = Column(JSON, default=list, comment="关键词列表")
    sources = Column(JSON, default=list, comment="监控数据源")
    severity = Column(
        SAEnum(AlertSeverity),
        default=AlertSeverity.MEDIUM,
        comment="严重程度",
    )
    notification_channels = Column(
        JSON,
        default=["email"],
        comment="通知渠道: email/slack/wechat/webhook",
    )
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    histories = relationship("AlertHistory", back_populates="rule", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AlertRule {self.name}>"


# ======================= 11. 预警历史 =======================
class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False, comment="预警标题")
    content = Column(Text, comment="预警内容")
    severity = Column(SAEnum(AlertSeverity), comment="严重程度")
    triggered_by = Column(String(300), comment="触发数据（来源URL）")
    source_data_id = Column(UUID(as_uuid=True), nullable=True, comment="关联原始数据 ID")
    is_read = Column(Boolean, default=False, index=True, comment="是否已读")
    is_resolved = Column(Boolean, default=False, comment="是否已处理")
    triggered_at = Column(DateTime, nullable=False, index=True, comment="触发时间")

    created_at = Column(DateTime, default=datetime.utcnow)

    rule = relationship("AlertRule", back_populates="histories")

    def __repr__(self):
        return f"<Alert {self.severity}: {self.title[:50]}>"


# ======================= 12. 系统用户 =======================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    display_name = Column(String(200))
    role = Column(String(50), default="viewer", comment="admin/analyst/viewer")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"
