<template>
  <div class="page">
    <div class="page-header">
      <h2>市场情报</h2>
      <p class="page-desc">收集和整理竞品市场动态，支持 AI 情感分析与摘要提取</p>
      <div class="header-actions">
        <el-button type="success" @click="handleBatchAISentiment" :loading="aiSentimentLoading">
          <el-icon><MagicStick /></el-icon>AI 情感分析
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>新增情报
        </el-button>
      </div>
    </div>

    <!-- 统计概览卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-num">{{ stats.total }}</div>
          <div class="stat-label">情报总数</div>
        </el-card>
      </el-col>
      <el-col :span="6" v-for="(count, cat) in stats.by_category" :key="cat">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-num">{{ count }}</div>
          <div class="stat-label">{{ categoryLabel(cat as string) }}</div>
        </el-card>
      </el-col>
      <el-col v-if="!Object.keys(stats.by_category).length" :span="18">
        <el-card shadow="hover" class="stat-card stat-empty">
          <span class="text-muted">暂无统计数据</span>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="handleSearch">
        <el-form-item label="关联竞品">
          <el-select
            v-model="filterForm.competitor_id"
            placeholder="全部竞品"
            clearable
            filterable
            style="width: 200px"
            @change="handleSearch"
          >
            <el-option
              v-for="c in competitorOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="情报分类">
          <el-select
            v-model="filterForm.category"
            placeholder="全部分类"
            clearable
            style="width: 160px"
            @change="handleSearch"
          >
            <el-option
              v-for="c in categories"
              :key="c.value"
              :label="c.label"
              :value="c.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="情感倾向">
          <el-select
            v-model="filterForm.sentiment"
            placeholder="全部"
            clearable
            style="width: 130px"
            @change="handleSearch"
          >
            <el-option label="正面" value="positive" />
            <el-option label="中性" value="neutral" />
            <el-option label="负面" value="negative" />
          </el-select>
        </el-form-item>
        <el-form-item label="重要度 ≥">
          <el-select
            v-model="filterForm.importance"
            placeholder="不限"
            clearable
            style="width: 100px"
            @change="handleSearch"
          >
            <el-option :label="n" :value="n" v-for="n in [1, 2, 3, 4, 5]" :key="n" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="标题/摘要搜索"
            clearable
            style="width: 200px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        style="width: 100%"
        empty-text="暂无情报数据"
        @row-click="openDetail"
        row-class-name="clickable-row"
      >
        <el-table-column prop="importance" label="重要度" width="90" align="center">
          <template #default="{ row }">
            <el-rate
              :model-value="row.importance"
              :max="5"
              disabled
              size="small"
              :colors="['#f56c6c', '#f56c6c', '#f56c6c']"
            />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="intel-title">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="competitor_name" label="关联竞品" width="130" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.category" size="small" :type="categoryTagType(row.category)">
              {{ row.category }}
            </el-tag>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="sentiment" label="情感" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.sentiment" size="small" :type="sentimentTagType(row.sentiment)">
              {{ sentimentLabel(row.sentiment) }}
            </el-tag>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="source_name" label="来源" width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <a v-if="row.source_url" :href="row.source_url" target="_blank" class="link">
              {{ row.source_name || '查看原文' }}
            </a>
            <span v-else>{{ row.source_name || '--' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="published_at" label="发布时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.published_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="openDetail(row)">详情</el-button>
            <el-button link type="primary" size="small" @click.stop="openEditDialog(row)">编辑</el-button>
            <el-popconfirm
              title="确认删除该情报？"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button link type="danger" size="small" @click.stop>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="fetchList"
          @size-change="fetchList"
        />
      </div>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailVisible"
      title="情报详情"
      size="520px"
      destroy-on-close
    >
      <template v-if="detailRow">
        <div class="detail-section">
          <div class="detail-header">
            <h3>{{ detailRow.title }}</h3>
            <div class="detail-meta">
              <el-rate
                :model-value="detailRow.importance"
                :max="5"
                disabled
                size="small"
              />
              <el-tag v-if="detailRow.sentiment" size="small" :type="sentimentTagType(detailRow.sentiment)">
                {{ sentimentLabel(detailRow.sentiment) }}
              </el-tag>
              <el-tag v-if="detailRow.category" size="small" :type="categoryTagType(detailRow.category)">
                {{ detailRow.category }}
              </el-tag>
            </div>
          </div>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="关联竞品">{{ detailRow.competitor_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ detailRow.source_name || '--' }}</el-descriptions-item>
            <el-descriptions-item label="发布时间">{{ formatDate(detailRow.published_at) }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(detailRow.created_at) }}</el-descriptions-item>
            <el-descriptions-item v-if="detailRow.source_url" label="来源链接" :span="2">
              <a :href="detailRow.source_url" target="_blank" class="link">{{ detailRow.source_url }}</a>
            </el-descriptions-item>
            <el-descriptions-item v-if="detailRow.tags?.length" label="标签" :span="2">
              <el-tag v-for="t in detailRow.tags" :key="t" size="small" class="tag-item">{{ t }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          <div v-if="detailRow.summary" class="detail-summary">
            <h4>情报摘要</h4>
            <p>{{ detailRow.summary }}</p>
          </div>
        </div>
      </template>
    </el-drawer>

    <!-- 新增/编辑 Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑情报' : '新增情报'"
      width="640px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="关联竞品" prop="competitor_id">
          <el-select
            v-model="formData.competitor_id"
            placeholder="选择竞品"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="c in competitorOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="情报标题" />
        </el-form-item>
        <el-form-item label="摘要" prop="summary">
          <el-input
            v-model="formData.summary"
            type="textarea"
            :rows="3"
            placeholder="情报摘要（可选）"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select
                v-model="formData.category"
                placeholder="选择分类"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="c in categories"
                  :key="c.value"
                  :label="c.label"
                  :value="c.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="情感倾向" prop="sentiment">
              <el-select
                v-model="formData.sentiment"
                placeholder="选择情感"
                clearable
                style="width: 100%"
              >
                <el-option label="正面" value="positive" />
                <el-option label="中性" value="neutral" />
                <el-option label="负面" value="negative" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="重要度" prop="importance">
          <el-rate v-model="formData.importance" :max="5" show-text />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="来源名称" prop="source_name">
              <el-input v-model="formData.source_name" placeholder="如: 36氪、TechCrunch" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="来源链接" prop="source_url">
              <el-input v-model="formData.source_url" placeholder="https://" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="发布时间" prop="published_at">
          <el-date-picker
            v-model="formData.published_at"
            type="datetime"
            placeholder="选择发布时间"
            style="width: 100%"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <el-select
            v-model="formData.tags"
            multiple
            filterable
            allow-create
            placeholder="输入标签后回车"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { intelligenceApi } from '@/api/intelligence'
import { competitorApi } from '@/api/competitors'
import { aiApi } from '@/api/ai'
import type { Intelligence, IntelligenceCreate, Competitor } from '@/types'

// ---------- 分类配置 ----------
const categories = [
  { value: 'product_update', label: '产品更新' },
  { value: 'funding', label: '融资动态' },
  { value: 'partnership', label: '合作动态' },
  { value: 'hr', label: '人事变动' },
  { value: 'policy', label: '政策法规' },
  { value: 'market_trend', label: '市场趋势' },
  { value: 'technology', label: '技术突破' },
  { value: 'other', label: '其他' },
]

const categoryLabelMap: Record<string, string> = {}
categories.forEach((c) => {
  categoryLabelMap[c.value] = c.label
})

const categoryTagMap: Record<string, string> = {
  product_update: 'success',
  funding: 'warning',
  partnership: '',
  hr: 'info',
  policy: 'danger',
  market_trend: '',
  technology: 'success',
  other: 'info',
}

function categoryLabel(cat: string) {
  return categoryLabelMap[cat] || cat
}

function categoryTagType(cat: string) {
  return categoryTagMap[cat] || ''
}

function sentimentLabel(s: string) {
  const map: Record<string, string> = { positive: '正面', neutral: '中性', negative: '负面' }
  return map[s] || s
}

function sentimentTagType(s: string) {
  const map: Record<string, string> = { positive: 'success', neutral: 'info', negative: 'danger' }
  return map[s] || ''
}

function formatDate(d: string | null) {
  if (!d) return '--'
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ---------- 统计 ----------
const stats = reactive<{
  total: number
  by_category: Record<string, number>
  by_sentiment: Record<string, number>
}>({
  total: 0,
  by_category: {},
  by_sentiment: {},
})

async function fetchStats() {
  try {
    const res = await intelligenceApi.stats()
    stats.total = res.data.total
    stats.by_category = res.data.by_category
    stats.by_sentiment = res.data.by_sentiment
  } catch {
    // ignore
  }
}

// ---------- 竞品选项 ----------
const competitorOptions = ref<{ id: string; name: string }[]>([])

async function fetchCompetitorOptions() {
  try {
    const res = await competitorApi.list({ page_size: 999 })
    competitorOptions.value = res.data.items.map((c: Competitor) => ({
      id: c.id,
      name: c.name,
    }))
  } catch {
    // ignore
  }
}

// ---------- 表格数据 ----------
const loading = ref(false)
const tableData = ref<Intelligence[]>([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const filterForm = reactive({
  competitor_id: '' as string,
  category: '' as string,
  sentiment: '' as string,
  importance: undefined as number | undefined,
  keyword: '',
})

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (filterForm.competitor_id) params.competitor_id = filterForm.competitor_id
    if (filterForm.category) params.category = filterForm.category
    if (filterForm.sentiment) params.sentiment = filterForm.sentiment
    if (filterForm.importance) params.importance = filterForm.importance
    if (filterForm.keyword) params.keyword = filterForm.keyword

    const res = await intelligenceApi.list(params)
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch {
    ElMessage.error('加载情报列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function resetFilter() {
  filterForm.competitor_id = ''
  filterForm.category = ''
  filterForm.sentiment = ''
  filterForm.importance = undefined
  filterForm.keyword = ''
  handleSearch()
}

// ---------- 详情抽屉 ----------
const detailVisible = ref(false)
const detailRow = ref<Intelligence | null>(null)

function openDetail(row: Intelligence) {
  detailRow.value = row
  detailVisible.value = true
}

// ---------- 弹窗表单 ----------
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref('')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

const defaultForm: IntelligenceCreate = {
  competitor_id: '',
  title: '',
  summary: '',
  category: '',
  sentiment: '',
  importance: 3,
  source_url: '',
  source_name: '',
  published_at: '',
  tags: [],
}

const formData = reactive<IntelligenceCreate>({ ...defaultForm })

const formRules: FormRules = {
  competitor_id: [{ required: true, message: '请选择关联竞品', trigger: 'change' }],
  title: [{ required: true, message: '请输入情报标题', trigger: 'blur' }],
}

function openCreateDialog() {
  isEdit.value = false
  editingId.value = ''
  Object.assign(formData, { ...defaultForm, tags: [] })
  dialogVisible.value = true
}

function openEditDialog(row: Intelligence) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(formData, {
    competitor_id: row.competitor_id,
    title: row.title,
    summary: row.summary || '',
    category: row.category || '',
    sentiment: row.sentiment || '',
    importance: row.importance,
    source_url: row.source_url || '',
    source_name: row.source_name || '',
    published_at: row.published_at || '',
    tags: row.tags ? [...row.tags] : [],
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await intelligenceApi.update(editingId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await intelligenceApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
    fetchStats()
  } catch {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitLoading.value = false
  }
}

// ---------- 删除 ----------
async function handleDelete(id: string) {
  try {
    await intelligenceApi.remove(id)
    ElMessage.success('已删除')
    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page--
    }
    fetchList()
    fetchStats()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ---------- AI 情感分析 ----------
const aiSentimentLoading = ref(false)

async function handleBatchAISentiment() {
  if (tableData.value.length === 0) {
    ElMessage.warning('暂无情报数据，请先添加情报')
    return
  }
  aiSentimentLoading.value = true
  try {
    // 对当前页的情报逐个进行情感分析
    const promises = tableData.value.map((intel) => {
      if (intel.sentiment && intel.sentiment !== 'neutral') {
        return Promise.resolve(null) // 已有情感标记的跳过
      }
      return aiApi.intelligenceSentiment(intel.id).catch(() => null)
    })
    const results = await Promise.all(promises)
    const updated = results.filter(Boolean).length
    if (updated > 0) {
      ElMessage.success(`已更新 ${updated} 条情报的情感标记`)
      fetchList()
      fetchStats()
    } else {
      ElMessage.info('当前情报已有情感标记，无需重复分析')
    }
  } catch {
    ElMessage.error('AI 情感分析失败')
  } finally {
    aiSentimentLoading.value = false
  }
}

onMounted(() => {
  fetchStats()
  fetchCompetitorOptions()
  fetchList()
})
</script>

<style scoped>
.page { padding: 0 10px; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 { margin: 0; }

.page-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: #909399;
  font-weight: 400;
}

.header-actions {
  display: flex;
  gap: 10px;
}

/* 统计卡片 */
.stats-row { margin-bottom: 16px; }

.stat-card { text-align: center; }
.stat-card :deep(.el-card__body) { padding: 18px 12px; }

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 6px;
}

.stat-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 76px;
}

/* 筛选 */
.filter-card { margin-bottom: 16px; }
.filter-card .el-form { margin-bottom: -8px; }

/* 表格 */
.intel-title { font-weight: 500; cursor: pointer; }

.clickable-row { cursor: pointer; }

.link {
  color: #409eff;
  text-decoration: none;
}

.link:hover { text-decoration: underline; }

.text-muted { color: #c0c4cc; }

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 详情 */
.detail-section { padding: 0; }

.detail-header {
  margin-bottom: 20px;
}

.detail-header h3 {
  margin: 0 0 12px;
  font-size: 18px;
  color: #303133;
  line-height: 1.4;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-summary {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.detail-summary h4 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #606266;
}

.detail-summary p {
  margin: 0;
  font-size: 14px;
  color: #303133;
  line-height: 1.7;
  white-space: pre-wrap;
}

.tag-item { margin-right: 6px; }
</style>
