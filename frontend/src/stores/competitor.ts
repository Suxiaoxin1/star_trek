import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { competitorApi } from '@/api/competitors'
import type {
  Competitor,
  CompetitorListParams,
  CompetitorCreate,
  CompetitorUpdate,
  Product,
  ProductCreate,
  Feature,
  FeatureCreate,
  PricingEntry,
} from '@/types'

export const useCompetitorStore = defineStore('competitor', () => {
  // ---------- 状态 ----------
  const list = ref<Competitor[]>([])
  const total = ref(0)
  const loading = ref(false)
  const current = ref<Competitor | null>(null)

  // ---------- 计算属性 ----------
  const activeCompetitors = computed(() => list.value.filter((c) => c.is_active))
  const directCompetitors = computed(() => list.value.filter((c) => c.tier === 'direct'))

  // ---------- 竞品 CRUD ----------
  async function fetchList(params?: CompetitorListParams) {
    loading.value = true
    try {
      const { data } = await competitorApi.list(params)
      list.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id: string) {
    loading.value = true
    try {
      const { data } = await competitorApi.get(id)
      current.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function create(payload: CompetitorCreate) {
    const { data } = await competitorApi.create(payload)
    list.value.unshift(data)
    return data
  }

  async function update(id: string, payload: CompetitorUpdate) {
    const { data } = await competitorApi.update(id, payload)
    const idx = list.value.findIndex((c) => c.id === id)
    if (idx > -1) list.value[idx] = data
    if (current.value?.id === id) current.value = data
    return data
  }

  async function remove(id: string, soft = true) {
    await competitorApi.remove(id, soft)
    if (soft) {
      const item = list.value.find((c) => c.id === id)
      if (item) item.is_active = false
    } else {
      list.value = list.value.filter((c) => c.id !== id)
    }
  }

  // ---------- 产品 ----------
  async function fetchProducts(competitorId: string): Promise<Product[]> {
    const { data } = await competitorApi.listProducts(competitorId)
    return data.items
  }

  async function createProduct(competitorId: string, payload: ProductCreate) {
    const { data } = await competitorApi.createProduct(competitorId, payload)
    return data
  }

  // ---------- 功能对比 ----------
  async function fetchFeatures(competitorId: string, category?: string) {
    const { data } = await competitorApi.listFeatures(competitorId, category)
    return data
  }

  async function upsertFeature(competitorId: string, payload: FeatureCreate) {
    const { data } = await competitorApi.upsertFeature(competitorId, payload)
    return data
  }

  // ---------- 价格历史 ----------
  async function fetchPricingHistory(competitorId: string) {
    const { data } = await competitorApi.listPricingHistory(competitorId)
    return data.items
  }

  return {
    // state
    list, total, loading, current,
    // computed
    activeCompetitors, directCompetitors,
    // actions
    fetchList, fetchDetail, create, update, remove,
    fetchProducts, createProduct,
    fetchFeatures, upsertFeature,
    fetchPricingHistory,
  }
})
