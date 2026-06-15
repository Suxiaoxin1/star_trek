import api from './index'
import type {
  Intelligence,
  IntelligenceCreate,
  IntelligenceListParams,
  IntelligenceStats,
} from '@/types'

export const intelApi = {
  list(params?: IntelligenceListParams) {
    return api.get<Paginated<Intelligence>>('/intelligence/', { params })
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
}
