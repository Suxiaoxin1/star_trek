import api from './index'
import type {
  Intelligence,
  IntelligenceCreate,
  IntelligenceListParams,
  IntelligenceStats,
} from '@/types'

export const intelligenceApi = {
  list(params?: IntelligenceListParams) {
    return api.get<{ items: Intelligence[]; total: number; page: number; page_size: number }>(
      '/intelligence/',
      { params },
    )
  },
  get(id: string) {
    return api.get<Intelligence>(`/intelligence/${id}`)
  },
  create(data: IntelligenceCreate) {
    return api.post<Intelligence>('/intelligence/', data)
  },
  update(id: string, data: IntelligenceCreate) {
    return api.put<Intelligence>(`/intelligence/${id}`, data)
  },
  stats() {
    return api.get<IntelligenceStats>('/intelligence/stats')
  },
  remove(id: string) {
    return api.delete(`/intelligence/${id}`)
  },
}

// @deprecated 向后兼容别名，确保 Vite 旧缓存不会报错
export const intelApi = intelligenceApi
