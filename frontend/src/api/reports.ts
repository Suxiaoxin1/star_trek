import api from './index'
import type { Report, ReportCreate } from '@/types'

export const reportApi = {
  list(params?: { status?: string; report_type?: string; page?: number; page_size?: number }) {
    return api.get<Paginated<Report>>('/reports/', { params })
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
}
