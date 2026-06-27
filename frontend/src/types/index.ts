// ==================== 通用 ====================
export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ==================== 竞品 ====================
export interface Competitor {
  id: string
  name: string
  name_en: string | null
  website: string | null
  logo_url: string | null
  tier: 'direct' | 'indirect' | 'potential'
  description: string | null
  headquarters: string | null
  founded_year: number | null
  employee_count: string | null
  funding_stage: string | null
  total_funding: string | null
  tags: string[]
  /** 扩展元数据，用于存储 LLM 技术参数（context_window、token 定价、合规标志等） */
  metadata: Record<string, any>
  is_active: boolean
  product_count: number
  intel_count: number
  products?: Product[]
  features?: Feature[]
  created_at: string
  updated_at: string
}

export interface CompetitorCreate {
  name: string
  name_en?: string
  website?: string
  logo_url?: string
  tier?: string
  description?: string
  headquarters?: string
  founded_year?: number
  employee_count?: string
  funding_stage?: string
  total_funding?: string
  tags?: string[]
  /** 扩展元数据（如 LLM 参数：flagship_model, context_window, input_price_per_1M 等） */
  metadata?: Record<string, any>
  is_active?: boolean
}

export type CompetitorUpdate = Partial<CompetitorCreate>

export interface CompetitorListParams {
  tier?: string
  is_active?: boolean
  keyword?: string
  page?: number
  page_size?: number
}

// ==================== 产品 ====================
export interface Product {
  id: string
  competitor_id: string
  name: string
  category: string | null
  description: string | null
  launch_date: string | null
  pricing_model: string | null
  target_market: string | null
  website: string | null
  tags: string[]
  /** 扩展元数据（LLM 参数：model_id, api_endpoint, max_tokens 等） */
  metadata: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProductCreate {
  name: string
  category?: string
  description?: string
  launch_date?: string
  pricing_model?: string
  target_market?: string
  website?: string
  tags?: string[]
  /** 扩展元数据 */
  metadata?: Record<string, any>
  is_active?: boolean
}

// ==================== 功能对比 ====================
export interface Feature {
  id: string
  competitor_id: string
  category: string
  feature_name: string
  support_level: 'full' | 'partial' | 'none' | 'unknown'
  description: string | null
  source_url: string | null
  verified_at: string | null
  created_at: string
  updated_at: string
}

export interface FeatureCreate {
  category: string
  feature_name: string
  support_level: string
  description?: string
  source_url?: string
}

// ==================== 价格历史 ====================
export interface PricingEntry {
  id: string
  competitor_id: string
  plan_name: string
  old_price: number | null
  new_price: number
  currency: string
  billing_cycle: string | null
  change_type: string | null
  change_description: string | null
  source_url: string | null
  detected_at: string
  created_at: string
}

export interface PricingCreate {
  plan_name: string
  old_price?: number
  new_price: number
  currency?: string
  billing_cycle?: string
  change_type?: string
  change_description?: string
  source_url?: string
  detected_at: string
}

// ==================== 市场情报 ====================
export interface Intelligence {
  id: string
  competitor_id: string
  competitor_name: string
  title: string
  summary: string | null
  category: string | null
  sentiment: string | null
  importance: number
  source_url: string | null
  source_name: string | null
  published_at: string | null
  tags: string[]
  created_at: string
  updated_at: string
}

export interface IntelligenceCreate {
  competitor_id: string
  title: string
  summary?: string
  category?: string
  sentiment?: string
  importance?: number
  source_url?: string
  source_name?: string
  published_at?: string
  tags?: string[]
}

export interface IntelligenceListParams {
  competitor_id?: string
  category?: string
  sentiment?: string
  importance?: number
  keyword?: string
  page?: number
  page_size?: number
}

export interface IntelligenceStats {
  total: number
  by_category: Record<string, number>
  by_sentiment: Record<string, number>
}

// ==================== 分析报告 ====================
export interface Report {
  id: string
  intelligence_id: string | null
  title: string
  content: string | null
  status: string
  report_type: string | null
  generated_by: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface ReportCreate {
  title: string
  content?: string
  status?: string
  report_type?: string
  intelligence_id?: string
  tags?: string[]
}

// ==================== 预警 ====================
export interface AlertRule {
  id: string
  name: string
  description: string | null
  target_type: string | null
  target_id: string | null
  keywords: string[]
  severity: string
  notification_channels: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AlertRuleCreate {
  name: string
  description?: string
  target_type?: string
  target_id?: string
  keywords?: string[]
  severity?: string
  notification_channels?: string[]
  is_active?: boolean
}

export interface AlertHistory {
  id: string
  rule_id: string
  rule_name: string
  title: string
  content: string | null
  severity: string | null
  is_read: boolean
  is_resolved: boolean
  triggered_at: string
  created_at: string
}

export interface AlertStats {
  unread_alerts: number
  unresolved_alerts: number
  active_rules: number
}

// ==================== 认证 ====================
export interface User {
  id: string
  username: string
  email: string
  display_name: string | null
  role: 'admin' | 'analyst' | 'viewer'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserRegister {
  username: string
  email: string
  password: string
  display_name?: string
  role?: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

// ==================== 数据源 ====================
export interface DataSource {
  id: string
  name: string
  source_type: 'rss' | 'api' | 'web_scraper' | 'social_media' | 'news' | 'manual'
  url: string | null
  crawl_config: Record<string, any>
  api_config: Record<string, any>
  is_active: boolean
  crawl_interval_minutes: number
  last_crawled_at: string | null
  last_status: string | null
  created_at: string
  updated_at: string
}

export interface DataSourceCreate {
  name: string
  source_type: string
  url?: string
  crawl_config?: Record<string, any>
  api_config?: Record<string, any>
  is_active?: boolean
  crawl_interval_minutes?: number
}

export type DataSourceUpdate = Partial<DataSourceCreate>

export interface DataSourceListParams {
  source_type?: string
  is_active?: boolean
  keyword?: string
  page?: number
  page_size?: number
}

export interface DataSourceStats {
  total: number
  active: number
  inactive: number
  by_type: Record<string, number>
  by_status: Record<string, number>
}

// ==================== 采集数据 ====================
export interface CollectedData {
  id: string
  source_id: string | null
  source_name: string
  title: string | null
  content: string | null
  content_hash: string | null
  url: string | null
  language: string
  raw_data: Record<string, any>
  collected_at: string
  processed: boolean
  created_at: string
}

export interface CollectedDataListParams {
  source_id?: string
  processed?: boolean
  keyword?: string
  language?: string
  page?: number
  page_size?: number
}

export interface CollectedDataStats {
  total: number
  processed: number
  unprocessed: number
  by_source: Record<string, number>
  by_language: Record<string, number>
  latest_collected_at: string | null
}

export interface CrawlTaskResult {
  task_id: string
  source_id?: string
  source_type?: string
  status: string
}

// ==================== AI 智能分析 ====================
export interface AIStatus {
  available: boolean
  model: string | null
  api_base: string
  message: string
}

export interface AISentimentResult {
  sentiment: string
  sentiment_score: number
  confidence: number
  key_phrases: string[]
  reasoning: string
}

export interface AISummaryResult {
  summary: string
  key_points: string[]
  impact_level: string
  affected_areas: string[]
  action_items: string[]
}

export interface AIReportGenerateParams {
  title?: string
  competitor_id?: string
  intelligence_ids?: string[]
  intelligence_limit?: number
  report_type?: string
  model?: string
  tags?: string[]
}

export interface AICompetitorResult {
  competitor_id: string
  competitor_name: string
  strengths: string[]
  weaknesses: string[]
  market_position: string
  threat_level: string
  opportunity_for_us: string[]
  strategic_recommendations: string[]
  recent_highlights: string[]
  risk_factors: string[]
}
