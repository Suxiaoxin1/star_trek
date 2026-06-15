-- ========================================
-- 自动化竞品分析与市场情报系统
-- 数据库初始化脚本
-- ========================================

-- 扩展：uuid-ossp（如需要）
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------
-- 1. 竞品
-- ------------------------------
CREATE TABLE IF NOT EXISTS competitors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    name_en         VARCHAR(200),
    website         VARCHAR(500),
    logo_url        VARCHAR(1000),
    tier            VARCHAR(20)  NOT NULL DEFAULT 'direct'
                        CHECK (tier IN ('direct', 'indirect', 'potential')),
    description     TEXT,
    headquarters    VARCHAR(200),
    founded_year    INTEGER,
    employee_count  VARCHAR(50),
    funding_stage   VARCHAR(100),
    total_funding   VARCHAR(100),
    tags            JSONB        DEFAULT '[]',
    metadata        JSONB        DEFAULT '{}',

    is_active       BOOLEAN      DEFAULT TRUE,
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_competitors_name   ON competitors (name);
CREATE INDEX ix_competitors_tier   ON competitors (tier);
CREATE INDEX ix_competitors_active ON competitors (is_active);

-- ------------------------------
-- 2. 竞品产品/服务
-- ------------------------------
CREATE TABLE IF NOT EXISTS products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id   UUID         NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    name            VARCHAR(300) NOT NULL,
    category        VARCHAR(100),
    description     TEXT,
    launch_date     TIMESTAMP,
    pricing_model   VARCHAR(200),
    target_market   VARCHAR(300),
    website         VARCHAR(500),
    tags            JSONB        DEFAULT '[]',
    metadata        JSONB        DEFAULT '{}',

    is_active       BOOLEAN      DEFAULT TRUE,
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_products_competitor ON products (competitor_id);
CREATE INDEX ix_products_category   ON products (category);

-- ------------------------------
-- 3. 竞品功能对比
-- ------------------------------
CREATE TABLE IF NOT EXISTS competitor_features (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id   UUID         NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    category        VARCHAR(100) NOT NULL,
    feature_name    VARCHAR(300) NOT NULL,
    support_level   VARCHAR(20)  DEFAULT 'unknown'
                        CHECK (support_level IN ('full', 'partial', 'none', 'unknown')),
    description     TEXT,
    source_url      VARCHAR(1000),
    verified_at     TIMESTAMP,

    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_features_competitor   ON competitor_features (competitor_id);
CREATE INDEX ix_features_category     ON competitor_features (category);
CREATE INDEX ix_features_name         ON competitor_features (feature_name);
CREATE UNIQUE INDEX ix_features_competitor_name ON competitor_features (competitor_id, feature_name);

-- ------------------------------
-- 4. 价格变动历史
-- ------------------------------
CREATE TABLE IF NOT EXISTS pricing_history (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id     UUID         NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    plan_name         VARCHAR(200) NOT NULL,
    old_price         DOUBLE PRECISION,
    new_price         DOUBLE PRECISION NOT NULL,
    currency          VARCHAR(10)  DEFAULT 'CNY',
    billing_cycle     VARCHAR(20),
    change_type       VARCHAR(20),
    change_description TEXT,
    source_url        VARCHAR(1000),
    detected_at       TIMESTAMP    NOT NULL,

    created_at        TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_pricing_competitor ON pricing_history (competitor_id);
CREATE INDEX ix_pricing_detected   ON pricing_history (detected_at);

-- ------------------------------
-- 5. 数据源
-- ------------------------------
CREATE TABLE IF NOT EXISTS data_sources (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  VARCHAR(300) NOT NULL,
    source_type           VARCHAR(30)  NOT NULL
                              CHECK (source_type IN ('rss', 'api', 'web_scraper', 'social_media', 'news', 'manual')),
    url                   VARCHAR(1000),
    crawl_config          JSONB        DEFAULT '{}',
    api_config            JSONB        DEFAULT '{}',

    is_active             BOOLEAN      DEFAULT TRUE,
    crawl_interval_minutes INTEGER     DEFAULT 360,
    last_crawled_at       TIMESTAMP,
    last_status           VARCHAR(20),

    created_at            TIMESTAMP    DEFAULT NOW(),
    updated_at            TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_sources_type   ON data_sources (source_type);
CREATE INDEX ix_sources_active ON data_sources (is_active);

-- ------------------------------
-- 6. 采集数据（原始）
-- ------------------------------
CREATE TABLE IF NOT EXISTS collected_data (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID         REFERENCES data_sources(id) ON DELETE SET NULL,
    title           VARCHAR(500),
    content         TEXT,
    content_hash    VARCHAR(64),
    url             VARCHAR(2000),
    language        VARCHAR(10)  DEFAULT 'zh',
    raw_data        JSONB        DEFAULT '{}',
    collected_at    TIMESTAMP    NOT NULL,
    processed       BOOLEAN      DEFAULT FALSE,

    created_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_collected_source   ON collected_data (source_id);
CREATE INDEX ix_collected_hash     ON collected_data (content_hash);
CREATE INDEX ix_collected_time     ON collected_data (collected_at);
CREATE INDEX ix_collected_processed ON collected_data (processed);
CREATE UNIQUE INDEX ix_collected_source_hash ON collected_data (source_id, content_hash);

-- ------------------------------
-- 7. 市场情报
-- ------------------------------
CREATE TABLE IF NOT EXISTS market_intelligence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id   UUID         NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL,
    summary         TEXT,
    category        VARCHAR(100),
    sentiment       VARCHAR(20),
    importance      INTEGER     DEFAULT 3 CHECK (importance BETWEEN 1 AND 5),
    source_url      VARCHAR(2000),
    source_name     VARCHAR(300),
    published_at    TIMESTAMP,
    tags            JSONB       DEFAULT '[]',
    metadata        JSONB       DEFAULT '{}',

    created_at      TIMESTAMP   DEFAULT NOW(),
    updated_at      TIMESTAMP   DEFAULT NOW()
);

CREATE INDEX ix_intel_competitor ON market_intelligence (competitor_id);
CREATE INDEX ix_intel_category   ON market_intelligence (category);
CREATE INDEX ix_intel_sentiment  ON market_intelligence (sentiment);
CREATE INDEX ix_intel_published  ON market_intelligence (published_at);

-- ------------------------------
-- 8. 分析报告
-- ------------------------------
CREATE TABLE IF NOT EXISTS analysis_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intelligence_id UUID         REFERENCES market_intelligence(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL,
    content         TEXT,
    status          VARCHAR(20)  DEFAULT 'draft'
                        CHECK (status IN ('draft', 'in_progress', 'completed', 'archived')),
    report_type     VARCHAR(100),
    generated_by    VARCHAR(50)  DEFAULT 'manual',
    ai_model        VARCHAR(100),
    ai_prompt       TEXT,
    tags            JSONB        DEFAULT '[]',
    metadata        JSONB        DEFAULT '{}',

    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_reports_intel   ON analysis_reports (intelligence_id);
CREATE INDEX ix_reports_status  ON analysis_reports (status);
CREATE INDEX ix_reports_type    ON analysis_reports (report_type);

-- ------------------------------
-- 9. 舆情数据
-- ------------------------------
CREATE TABLE IF NOT EXISTS sentiment_data (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id    UUID         NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    platform         VARCHAR(100),
    content          TEXT         NOT NULL,
    author           VARCHAR(200),
    sentiment        VARCHAR(20),
    sentiment_score  DOUBLE PRECISION,
    engagement_count INTEGER     DEFAULT 0,
    published_at     TIMESTAMP,
    source_url       VARCHAR(2000),

    created_at       TIMESTAMP   DEFAULT NOW()
);

CREATE INDEX ix_sentiment_competitor ON sentiment_data (competitor_id);
CREATE INDEX ix_sentiment_platform   ON sentiment_data (platform);
CREATE INDEX ix_sentiment_type       ON sentiment_data (sentiment);
CREATE INDEX ix_sentiment_published  ON sentiment_data (published_at);

-- ------------------------------
-- 10. 预警规则
-- ------------------------------
CREATE TABLE IF NOT EXISTS alert_rules (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  VARCHAR(300) NOT NULL,
    description           TEXT,
    target_type           VARCHAR(50),
    target_id             UUID,
    keywords              JSONB        DEFAULT '[]',
    sources               JSONB        DEFAULT '[]',
    severity              VARCHAR(20)  DEFAULT 'medium'
                              CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    notification_channels JSONB        DEFAULT '["email"]',
    is_active             BOOLEAN      DEFAULT TRUE,

    created_at            TIMESTAMP    DEFAULT NOW(),
    updated_at            TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_alerts_active ON alert_rules (is_active);

-- ------------------------------
-- 11. 预警历史
-- ------------------------------
CREATE TABLE IF NOT EXISTS alert_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id         UUID         NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL,
    content         TEXT,
    severity        VARCHAR(20)
                        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    triggered_by    VARCHAR(300),
    source_data_id  UUID,
    is_read         BOOLEAN     DEFAULT FALSE,
    is_resolved     BOOLEAN     DEFAULT FALSE,
    triggered_at    TIMESTAMP   NOT NULL,

    created_at      TIMESTAMP   DEFAULT NOW()
);

CREATE INDEX ix_alert_hist_rule    ON alert_history (rule_id);
CREATE INDEX ix_alert_hist_trigger ON alert_history (triggered_at);
CREATE INDEX ix_alert_hist_read    ON alert_history (is_read);

-- ------------------------------
-- 12. 系统用户
-- ------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(100) NOT NULL UNIQUE,
    email           VARCHAR(320) NOT NULL UNIQUE,
    hashed_password VARCHAR(200) NOT NULL,
    display_name    VARCHAR(200),
    role            VARCHAR(50)  DEFAULT 'viewer'
                        CHECK (role IN ('admin', 'analyst', 'viewer')),
    is_active       BOOLEAN      DEFAULT TRUE,

    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX ix_users_username ON users (username);
CREATE INDEX ix_users_email    ON users (email);

-- ========================================
-- 示例种子数据 (仅开发环境)
-- ========================================
-- INSERT INTO competitors (name, name_en, website, tier, description)
-- VALUES
--     ('示例竞品A', 'Example A', 'https://example-a.com', 'direct', '主要竞品示例'),
--     ('示例竞品B', 'Example B', 'https://example-b.com', 'indirect', '间接竞品');
