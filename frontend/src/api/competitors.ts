import api from './index'
import type {
  Competitor,
  CompetitorCreate,
  CompetitorUpdate,
  CompetitorListParams,
  Product,
  ProductCreate,
  Feature,
  FeatureCreate,
  PricingEntry,
  PricingCreate,
} from '@/types'

export const competitorApi = {
  // ---------- 竞品 CRUD ----------
  list(params?: CompetitorListParams) {
    return api.get<Paginated<Competitor>>('/competitors/', { params })
  },
  get(id: string) {
    return api.get<Competitor>(`/competitors/${id}`)
  },
  create(data: CompetitorCreate) {
    return api.post<Competitor>('/competitors/', data)
  },
  update(id: string, data: CompetitorUpdate) {
    return api.put<Competitor>(`/competitors/${id}`, data)
  },
  remove(id: string, soft = true) {
    return api.delete(`/competitors/${id}`, { params: { soft } })
  },

  // ---------- 产品 ----------
  listProducts(competitorId: string) {
    return api.get<Paginated<Product>>(`/competitors/${competitorId}/products`)
  },
  createProduct(competitorId: string, data: ProductCreate) {
    return api.post<Product>(`/competitors/${competitorId}/products`, data)
  },

  // ---------- 功能对比 ----------
  listFeatures(competitorId: string, category?: string) {
    return api.get<{ items: Feature[]; total: number; categories: Record<string, Feature[]> }>(
      `/competitors/${competitorId}/features`,
      { params: category ? { category } : {} },
    )
  },
  upsertFeature(competitorId: string, data: FeatureCreate) {
    return api.post<Feature>(`/competitors/${competitorId}/features`, data)
  },

  // ---------- 价格历史 ----------
  listPricingHistory(competitorId: string) {
    return api.get<Paginated<PricingEntry>>(`/competitors/${competitorId}/pricing-history`)
  },
  recordPricing(competitorId: string, data: PricingCreate) {
    return api.post<PricingEntry>(`/competitors/${competitorId}/pricing-history`, data)
  },
}
