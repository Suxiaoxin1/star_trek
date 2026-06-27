import api from './index'
import type { Report, ReportCreate } from '@/types'

export const reportApi = {
  list(params?: { status?: string; report_type?: string; page?: number; page_size?: number }) {
    return api.get<{ items: Report[]; total: number; page: number; page_size: number }>(
      '/reports/',
      { params },
    )
  },
  get(id: string) {
    return api.get<Report>(`/reports/${id}`)
  },
  create(data: ReportCreate) {
    return api.post<Report>('/reports/', data)
  },
  update(id: string, data: ReportCreate) {
    return api.put<Report>(`/reports/${id}`, data)
  },
  remove(id: string) {
    return api.delete(`/reports/${id}`)
  },
}
