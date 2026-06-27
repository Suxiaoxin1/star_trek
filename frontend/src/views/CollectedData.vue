<template>
  <div class="collected-data-page">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-total">
          <div class="stat-icon"><el-icon><DataLine /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">{{ stats.total }}</div>
            <div class="stat-label">采集总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-processed">
          <div class="stat-icon"><el-icon><CircleCheck /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">{{ stats.processed }}</div>
            <div class="stat-label">已处理</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-unprocessed">
          <div class="stat-icon"><el-icon><Clock /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num">{{ stats.unprocessed }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card stat-latest">
          <div class="stat-icon"><el-icon><Timer /></el-icon></div>
          <div class="stat-body">
            <div class="stat-num stat-num-sm">{{ stats.latest_collected_at ? formatTime(stats.latest_collected_at) : '-' }}</div>
            <div class="stat-label">最近采集</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" class="filter-form" @submit.prevent="handleSearch">
        <el-form-item label="数据源">
          <el-select
            v-model="filters.source_id"
            placeholder="全部"
            clearable
            filterable
            style="width: 160px"
            @change="handleSearch"
          >
            <el-option v-for="s in sourceOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filters.processed"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option label="待处理" value="false" />
            <el-option label="已处理" value="true" />
          </el-select>
        </el-form-item>
        <el-form-item label="语言">
          <el-select
            v-model="filters.language"
            placeholder="全部"
            clearable
            style="width: 100px"
            @change="handleSearch"
          >
            <el-option label="中文" value="zh" />
            <el-option label="英文" value="en" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索标题..."
            clearable
            style="width: 200px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon><span class="btn-text">搜索</span>
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon><span class="btn-text">重置</span>
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据列表 -->
    <el-card>
      <el-table
        :data="items"
        v-loading="loading"
        stripe
        style="width: 100%"
        row-key="id"
        :expand-row-keys="expandedRowKeys"
        @expand-change="handleExpandChange"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-content">
              <div v-if="row.content" class="expand-section">
                <h4 class="expand-title">内容详情</h4>
                <div class="content-text">{{ row.content }}</div>
              </div>
              <el-divider v-if="row.content && row.raw_data" />
              <div v-if="row.raw_data && Object.keys(row.raw_data).length" class="expand-section">
                <h4 class="expand-title">原始数据</h4>
                <pre class="raw-data">{{ JSON.stringify(row.raw_data, null, 2) }}</pre>
              </div>
              <div v-if="!row.content && !row.raw_data" class="expand-empty">
                暂无详细数据
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="250" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.title || '(无标题)' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source_name" label="数据源" width="150">
          <template #default="{ row }">
            <span>{{ row.source_name || '--' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="链接" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <a v-if="row.url" :href="row.url" target="_blank" rel="noopener" class="link">
              {{ row.url }}
            </a>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="language" label="语言" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.language === 'zh' ? '' : 'info'" effect="plain">
              {{ row.language === 'zh' ? '中文' : row.language === 'en' ? '英文' : row.language }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="processed" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.processed ? 'success' : 'warning'">
              {{ row.processed ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="collected_at" label="采集时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.collected_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.processed"
              size="small"
              type="success"
              plain
              :loading="row._marking"
              @click="handleMarkProcessed(row)"
            >
              标记处理
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              :icon="Delete"
              @click="handleDelete(row)"
            />
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无采集数据" :image-size="120" />
        </template>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        class="pagination"
        :background="true"
        :small="isMobile"
        @current-change="loadList"
        @size-change="handleSizeChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Refresh, Delete, DataLine, CircleCheck, Clock, Timer,
} from '@element-plus/icons-vue'
import { collectedDataApi, datasourceApi } from '@/api/datasources'
import type { CollectedData, CollectedDataStats, DataSource } from '@/types'

// ==================== 响应式判断 ====================
const isMobile = computed(() => window.innerWidth < 768)

// ==================== 状态 ====================
const loading = ref(false)
const items = ref<CollectedData[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const stats = ref<CollectedDataStats>({
  total: 0, processed: 0, unprocessed: 0,
  by_source: {}, by_language: {}, latest_collected_at: null,
})
const sourceOptions = ref<DataSource[]>([])
const expandedRowKeys = ref<string[]>([])

const filters = reactive({
  source_id: '',
  processed: '',
  language: '',
  keyword: '',
})

// ==================== 工具函数 ====================
function formatTime(t: string | null): string {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

function buildParams() {
  const params: Record<string, unknown> = {
    page: page.value,
    page_size: pageSize.value,
  }
  if (filters.source_id) params.source_id = filters.source_id
  if (filters.processed !== '') params.processed = filters.processed === 'true'
  if (filters.language) params.language = filters.language
  if (filters.keyword) params.keyword = filters.keyword
  return params
}

// ==================== 数据加载 ====================
async function loadList() {
  loading.value = true
  try {
    const { data } = await collectedDataApi.list(buildParams())
    items.value = data.items
    total.value = data.total
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const { data } = await collectedDataApi.stats()
    stats.value = data
  } catch {
    // 统计加载失败不阻塞主流程
  }
}

async function loadSourceOptions() {
  try {
    const { data } = await datasourceApi.list({ page_size: 100 })
    sourceOptions.value = data.items
  } catch {
    // 数据源选项加载失败不阻塞主流程
  }
}

// ==================== 交互处理 ====================
function handleSearch() {
  page.value = 1
  expandedRowKeys.value = []
  loadList()
}

function handleReset() {
  filters.source_id = ''
  filters.processed = ''
  filters.language = ''
  filters.keyword = ''
  page.value = 1
  expandedRowKeys.value = []
  loadList()
}

function handleSizeChange() {
  page.value = 1
  expandedRowKeys.value = []
  loadList()
}

function handleExpandChange(row: CollectedData, expandedRows: CollectedData[]) {
  expandedRowKeys.value = expandedRows.map(r => r.id)
}

async function handleMarkProcessed(row: any) {
  row._marking = true
  try {
    await collectedDataApi.markProcessed(row.id)
    ElMessage.success('已标记为已处理')
    row.processed = true
    stats.value.processed++
    stats.value.unprocessed--
  } catch (e: any) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    row._marking = false
  }
}

async function handleDelete(row: CollectedData) {
  await ElMessageBox.confirm('确定删除此条采集数据？', '确认删除', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  try {
    await collectedDataApi.remove(row.id)
    ElMessage.success('已删除')
    // 本地移除，避免重新请求
    items.value = items.value.filter(item => item.id !== row.id)
    total.value--
    stats.value.total--
    if (!row.processed) stats.value.unprocessed--
    else stats.value.processed--
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

// ==================== 初始化 ====================
onMounted(() => {
  // 并行加载，互不阻塞
  Promise.allSettled([loadList(), loadStats(), loadSourceOptions()])
})
</script>

<style scoped>
/* ==================== 页面容器 ==================== */
.collected-data-page {
  padding: 0;
}

/* ==================== 统计卡片 ==================== */
.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 20px;
}

.stat-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-total .stat-icon { background: linear-gradient(135deg, #409eff, #66b1ff); }
.stat-processed .stat-icon { background: linear-gradient(135deg, #67c23a, #85ce61); }
.stat-unprocessed .stat-icon { background: linear-gradient(135deg, #e6a23c, #f0c78a); }
.stat-latest .stat-icon { background: linear-gradient(135deg, #909399, #b1b3b8); }

.stat-body {
  flex: 1;
  min-width: 0;
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-num-sm {
  font-size: 15px;
  font-weight: 600;
  color: #409eff;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

/* ==================== 筛选栏 ==================== */
.filter-card {
  margin-bottom: 16px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 8px;
}

/* ==================== 表格 ==================== */
.link {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.link:hover {
  text-decoration: underline;
}

.text-muted {
  color: #c0c4cc;
}

/* ==================== 展开行 ==================== */
.expand-content {
  padding: 16px 24px;
  max-width: 900px;
}

.expand-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin: 0 0 8px 0;
}

.expand-section {
  margin-bottom: 8px;
}

.content-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.8;
  font-size: 14px;
  color: #303133;
  max-height: 400px;
  overflow-y: auto;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.raw-data {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  overflow-x: auto;
  max-height: 240px;
  margin: 0;
  line-height: 1.6;
  color: #606266;
}

.expand-empty {
  text-align: center;
  color: #c0c4cc;
  padding: 24px 0;
  font-size: 14px;
}

/* ==================== 分页 ==================== */
.pagination {
  margin-top: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

/* ==================== 响应式 ==================== */
@media (max-width: 768px) {
  .stats-row {
    margin-bottom: 12px;
  }

  .stat-card :deep(.el-card__body) {
    padding: 14px;
    gap: 12px;
  }

  .stat-icon {
    width: 36px;
    height: 36px;
    font-size: 18px;
    border-radius: 8px;
  }

  .stat-num {
    font-size: 22px;
  }

  .stat-num-sm {
    font-size: 13px;
  }

  .stat-label {
    font-size: 12px;
  }

  .filter-form {
    flex-direction: column;
  }

  .filter-form :deep(.el-form-item) {
    width: 100%;
    margin-right: 0;
  }

  .btn-text {
    display: none;
  }

  .expand-content {
    padding: 12px;
  }
}
</style>
