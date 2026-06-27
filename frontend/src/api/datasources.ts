import api from './index'
import type {
  DataSource,
  DataSourceCreate,
  DataSourceUpdate,
  DataSourceListParams,
  DataSourceStats,
  CollectedData,
  CollectedDataListParams,
  CollectedDataStats,
  CrawlTaskResult,
  Paginated,
} from '@/types'

export const datasourceApi = {
  // ---------- 数据源 CRUD ----------
  list(params?: DataSourceListParams) {
    return api.get<Paginated<DataSource>>('/datasources/', { params })
  },
  get(id: string) {
    return api.get<DataSource>(`/datasources/${id}`)
  },
  create(data: DataSourceCreate) {
    return api.post<DataSource>('/datasources/', data)
  },
  update(id: string, data: DataSourceUpdate) {
    return api.put<DataSource>(`/datasources/${id}`, data)
  },
  remove(id: string) {
    return api.delete(`/datasources/${id}`)
  },

  // ---------- 采集操作 ----------
  triggerCrawl(id: string) {
    return api.post<CrawlTaskResult>(`/datasources/${id}/crawl`)
  },
  triggerCrawlAll() {
    return api.post<CrawlTaskResult>('/datasources/crawl-all')
  },
  triggerCrawlByType(sourceType: string) {
    return api.post<CrawlTaskResult>(`/datasources/crawl-by-type/${sourceType}`)
  },

  // ---------- 统计 ----------
  stats() {
    return api.get<DataSourceStats>('/datasources/stats')
  },
}

export const collectedDataApi = {
  // ---------- 采集数据 ----------
  list(params?: CollectedDataListParams) {
    return api.get<Paginated<CollectedData>>('/collected-data/', { params })
  },
  get(id: string) {
    return api.get<CollectedData>(`/collected-data/${id}`)
  },
  markProcessed(id: string) {
    return api.put(`/collected-data/${id}/process`)
  },
  remove(id: string) {
    return api.delete(`/collected-data/${id}`)
  },
  stats() {
    return api.get<CollectedDataStats>('/collected-data/stats')
  },
}