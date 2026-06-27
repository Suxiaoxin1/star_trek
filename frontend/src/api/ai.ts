import api from './index'
import type { Report } from '@/types'

// ────────────── AI 状态 ──────────────
export const aiApi = {
  /** 检查 AI 服务状态 */
  status() {
    return api.get<AIStatus>('/ai/status')
  },

  /** 单条情感分析 */
  sentiment(text: string, model?: string) {
    return api.post<AISentimentResult>('/ai/sentiment', { text, model })
  },

  /** 批量情感分析 */
  sentimentBatch(texts: string[], model?: string) {
    return api.post<AISentimentResult[]>('/ai/sentiment/batch', { texts, model })
  },

  /** 对指定情报进行情感分析 */
  intelligenceSentiment(intelId: string) {
    return api.post<AISentimentResult & { intelligence_id: string; title: string }>(
      `/ai/sentiment/intelligence/${intelId}`,
    )
  },

  /** 摘要提取 */
  summary(text: string, model?: string) {
    return api.post<AISummaryResult>('/ai/summary', { text, model })
  },

  /** 对指定情报提取摘要 */
  intelligenceSummary(intelId: string) {
    return api.post<AISummaryResult & { intelligence_id: string; title: string }>(
      `/ai/summary/intelligence/${intelId}`,
    )
  },

  /** AI 生成分析报告（同步） */
  generateReport(params: AIReportGenerateParams) {
    return api.post<Report>('/ai/report/generate', params)
  },

  /** AI 流式生成报告（返回 fetch 用于 SSE） */
  streamReport(params: AIReportGenerateParams) {
    const token = localStorage.getItem('ci_access_token')
    const baseURL = api.defaults.baseURL || '/api/v1'

    return fetch(`${baseURL}/ai/report/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify(params),
    })
  },

  /** 竞品深度分析 */
  competitorAnalysis(competitorId: string, intelligenceLimit?: number, model?: string) {
    return api.post<AICompetitorResult>('/ai/competitor', {
      competitor_id: competitorId,
      intelligence_limit: intelligenceLimit,
      model,
    })
  },
}

// ────────────── 类型定义 ──────────────
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