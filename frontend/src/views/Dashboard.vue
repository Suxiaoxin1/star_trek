<template>
  <div class="dashboard">
    <h2>仪表盘</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.competitors" @click="router.push('/competitors')">
          <div class="stat-value">{{ stats.competitors }}</div>
          <div class="stat-label">监控竞品</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.intel" @click="router.push('/intelligence')">
          <div class="stat-value">{{ stats.intelTotal }}</div>
          <div class="stat-label">情报条目</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.competitors" @click="router.push('/alerts')">
          <div class="stat-value">{{ stats.activeRules }}</div>
          <div class="stat-label">活跃预警规则</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" v-loading="loading.alerts" @click="router.push('/alerts')">
          <div class="stat-value" :class="{ 'stat-warn': stats.unreadAlerts > 0 }">{{ stats.unreadAlerts }}</div>
          <div class="stat-label">未读预警</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>情报分类分布</span>
              <span v-if="!loading.intel" class="card-sub">共 {{ stats.intelTotal }} 条</span>
            </div>
          </template>
          <div v-if="loading.intel" class="chart-placeholder"><el-icon :size="24" class="is-loading"><Loading /></el-icon></div>
          <div v-else-if="intelCategories.length === 0" class="chart-placeholder">
            <el-empty description="暂无情报数据" :image-size="80" />
          </div>
          <div v-else class="category-grid">
            <div v-for="cat in intelCategories" :key="cat.name" class="category-item">
              <div class="category-name">{{ cat.name || '未分类' }}</div>
              <el-progress :percentage="cat.percent" :color="cat.color" :stroke-width="16" />
              <span class="category-count">{{ cat.value }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最新动态</span>
            </div>
          </template>
          <div v-if="loading.intel" class="chart-placeholder">
            <el-icon :size="24" class="is-loading"><Loading /></el-icon>
          </div>
          <div v-else-if="recentIntel.length === 0" class="chart-placeholder">
            <el-empty description="暂无动态" :image-size="80" />
          </div>
          <el-timeline v-else>
            <el-timeline-item
              v-for="item in recentIntel"
              :key="item.id"
              :timestamp="formatDate(item.published_at || item.created_at)"
              :color="sentimentColor(item.sentiment)"
            >
              <div class="timeline-item">
                <span class="timeline-title">{{ item.title }}</span>
                <span class="timeline-source">{{ item.competitor_name }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { competitorApi } from '@/api/competitors'
import { intelligenceApi } from '@/api/intelligence'
import { alertApi } from '@/api/alerts'

const router = useRouter()

// ---------- 加载 & 统计 ----------
const loading = reactive({
  competitors: false,
  intel: false,
  alerts: false,
})

const stats = reactive({
  competitors: 0,
  intelTotal: 0,
  unreadAlerts: 0,
  activeRules: 0,
})

const intelCategories = ref<{ name: string; value: number; percent: number; color: string }[]>([])
const recentIntel = ref<any[]>([])

const categoryColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#b37feb', '#36cfc9', '#ff85c0']

async function loadStats() {
  // 并行加载所有数据
  loading.competitors = true
  loading.intel = true
  loading.alerts = true

  try {
    const [compRes, intelStatsRes, alertStatsRes, recentRes] = await Promise.all([
      competitorApi.list({ page: 1, page_size: 1 }),
      intelligenceApi.stats(),
      alertApi.stats(),
      intelligenceApi.list({ page: 1, page_size: 8 }),
    ])

    // 竞品数量
    stats.competitors = compRes.data.total

    // 情报统计
    const is = intelStatsRes.data
    stats.intelTotal = is.total || 0

    // 分类分布
    const catMap: Record<string, number> = is.by_category || {}
    const entries = Object.entries(catMap)
    const maxCount = Math.max(1, ...Object.values(catMap))
    intelCategories.value = entries.map(([name, value], i) => ({
      name,
      value: value as number,
      percent: Math.round(((value as number) / maxCount) * 100),
      color: categoryColors[i % categoryColors.length],
    }))

    // 预警统计
    stats.unreadAlerts = alertStatsRes.data.unread_alerts || 0
    stats.activeRules = alertStatsRes.data.active_rules || 0

    // 最新情报
    recentIntel.value = recentRes.data.items || []
  } catch {
    // 静默处理，卡片显示 0
  } finally {
    loading.competitors = false
    loading.intel = false
    loading.alerts = false
  }
}

// ---------- 工具 ----------
const sentimentColorMap: Record<string, string> = {
  positive: '#67c23a',
  neutral: '#909399',
  negative: '#f56c6c',
}
function sentimentColor(s: string | null) {
  return s ? sentimentColorMap[s] || '#909399' : '#909399'
}

function formatDate(d: string) {
  if (!d) return '--'
  return new Date(d).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.dashboard { padding: 0 10px; }

.stat-row { margin-bottom: 20px; }

.stat-card { text-align: center; cursor: pointer; transition: transform 0.2s; }
.stat-card:hover { transform: translateY(-2px); }

.stat-value { font-size: 32px; font-weight: bold; color: #409eff; }
.stat-value.stat-warn { color: #e6a23c; }

.stat-label { font-size: 14px; color: #909399; margin-top: 8px; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-sub { font-size: 13px; color: #909399; }

.chart-placeholder {
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  background: #fafafa;
  border-radius: 4px;
}

.category-grid { padding: 8px 0; }

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.category-name {
  width: 80px;
  font-size: 13px;
  color: #606266;
  text-align: right;
  flex-shrink: 0;
}

.category-item .el-progress { flex: 1; }

.category-count {
  width: 36px;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  text-align: left;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.timeline-title {
  font-size: 13px;
  color: #303133;
  line-height: 1.4;
}

.timeline-source {
  font-size: 12px;
  color: #909399;
}
</style>
