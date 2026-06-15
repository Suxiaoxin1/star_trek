import api from './index'
import type { AlertRule, AlertRuleCreate, AlertHistory, AlertStats } from '@/types'

export const alertApi = {
  // ---------- 规则 ----------
  listRules(params?: { is_active?: boolean }) {
    return api.get<Paginated<AlertRule>>('/alerts/rules', { params })
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
  listHistory(params?: { page?: number; page_size?: number; is_read?: boolean; severity?: string }) {
    return api.get<Paginated<AlertHistory>>('/alerts/history', { params })
  },
  markRead(id: string) {
    return api.put(`/alerts/history/${id}/read`)
  },
  resolve(id: string) {
    return api.put(`/alerts/history/${id}/resolve`)
  },

  // ---------- 统计 ----------
  stats() {
    return api.get<AlertStats>('/alerts/stats')
  },
}
