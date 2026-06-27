import api from './index'
import type {
  AlertRule,
  AlertRuleCreate,
  AlertHistory,
  AlertStats,
} from '@/types'

export const alertApi = {
  // ---------- 规则 ----------
  listRules(is_active?: boolean) {
    return api.get<{ items: AlertRule[]; total: number }>('/alerts/rules', {
      params: is_active !== undefined ? { is_active } : {},
    })
  },
  createRule(data: AlertRuleCreate) {
    return api.post<AlertRule>('/alerts/rules', data)
  },
  updateRule(id: string, data: AlertRuleCreate) {
    return api.put<AlertRule>(`/alerts/rules/${id}`, data)
  },
  deleteRule(id: string) {
    return api.delete(`/alerts/rules/${id}`)
  },

  // ---------- 历史 ----------
  listHistory(params?: {
    rule_id?: string
    is_read?: boolean
    severity?: string
    page?: number
    page_size?: number
  }) {
    return api.get<{ items: AlertHistory[]; total: number; page: number; page_size: number }>(
      '/alerts/history',
      { params },
    )
  },
  markRead(id: string) {
    return api.put(`/alerts/history/${id}/read`)
  },
  resolveAlert(id: string) {
    return api.put(`/alerts/history/${id}/resolve`)
  },

  // ---------- 统计 ----------
  stats() {
    return api.get<AlertStats>('/alerts/stats')
  },
}
