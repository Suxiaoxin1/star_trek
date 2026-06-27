<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <div class="stat-card gradient-blue" v-loading="loading.competitors" @click="router.push('/competitors')">
          <div class="stat-icon-wrap">
            <el-icon :size="28"><OfficeBuilding /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.competitors }}</div>
            <div class="stat-label">监控竞品</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card gradient-green" v-loading="loading.intel" @click="router.push('/intelligence')">
          <div class="stat-icon-wrap">
            <el-icon :size="28"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.intelTotal }}</div>
            <div class="stat-label">情报条目</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card gradient-orange" v-loading="loading.alerts" @click="router.push('/alerts')">
          <div class="stat-icon-wrap">
            <el-icon :size="28"><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.activeRules }}</div>
            <div class="stat-label">活跃预警规则</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card gradient-red" v-loading="loading.alerts" @click="router.push('/alerts')">
          <div class="stat-icon-wrap">
            <el-icon :size="28"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" :class="{ 'value-warn': stats.unreadAlerts > 0 }">{{ stats.unreadAlerts }}</div>
            <div class="stat-label">未读预警</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card class="quick-actions" shadow="never">
      <template #header>
        <span class="section-title">快捷操作</span>
      </template>
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="action-item" @click="router.push('/competitors')">
            <el-icon :size="22" color="#409eff"><Plus /></el-icon>
            <span>新增竞品</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="action-item" @click="router.push('/intelligence')">
            <el-icon :size="22" color="#67c23a"><EditPen /></el-icon>
            <span>添加情报</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="action-item" @click="router.push('/ai-analysis')">
            <el-icon :size="22" color="#e6a23c"><MagicStick /></el-icon>
            <span>AI 分析</span>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="action-item" @click="router.push('/datasources')">
            <el-icon :size="22" color="#909399"><Link /></el-icon>
            <span>配置数据源</span>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span class="section-title">情报分类分布</span>
              <span v-if="!loading.intel" class="card-sub">共 {{ stats.intelTotal }} 条</span>
            </div>
          </template>
          <div v-if="loading.intel" class="chart-placeholder"><el-icon :size="24" class="is-loading"><Loading /></el-icon></div>
          <div v-else-if="intelCategories.length === 0" class="chart-placeholder">
            <el-empty description="暂无情报数据">
              <el-button type="primary" size="small" @click="router.push('/intelligence')">添加情报</el-button>
            </el-empty>
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
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span class="section-title">最新动态</span>
              <el-button v-if="recentIntel.length > 0" link type="primary" size="small" @click="router.push('/intelligence')">查看全部</el-button>
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

    stats.competitors = compRes.data.total

    const is = intelStatsRes.data
    stats.intelTotal = is.total || 0

    const catMap: Record<string, number> = is.by_category || {}
    const entries = Object.entries(catMap)
    const maxCount = Math.max(1, ...Object.values(catMap))
    intelCategories.value = entries.map(([name, value], i) => ({
      name,
      value: value as number,
      percent: Math.round(((value as number) / maxCount) * 100),
      color: categoryColors[i % categoryColors.length],
    }))

    stats.unreadAlerts = alertStatsRes.data.unread_alerts || 0
    stats.activeRules = alertStatsRes.data.active_rules || 0

    recentIntel.value = recentRes.data.items || []
  } catch {
    // 静默处理
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

/* ===== 统计卡片 ===== */
.stat-row { margin-bottom: 20px; }

.stat-card {
  display: flex;
  align-items: center;
  padding: 24px 20px;
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  min-height: 100px;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.stat-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  margin-left: 16px;
}

.stat-value {
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
}

.value-warn {
  color: #fff;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

.stat-label {
  font-size: 13px;
  opacity: 0.85;
  margin-top: 4px;
}

/* 渐变背景 */
.gradient-blue {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
}
.gradient-green {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
}
.gradient-orange {
  background: linear-gradient(135deg, #e6a23c 0%, #cf8e24 100%);
}
.gradient-red {
  background: linear-gradient(135deg, #f56c6c 0%, #dd4a4a 100%);
}

/* ===== 快捷操作 ===== */
.quick-actions { margin-bottom: 0; }

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.action-item:hover {
  background: #f5f7fa;
}

/* ===== 卡片 ===== */
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
  border-radius: 8px;
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
