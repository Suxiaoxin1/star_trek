<template>
  <div class="page">
    <div class="page-header">
      <h2>分析报告</h2>
      <div class="header-actions">
        <el-button type="success" @click="router.push('/ai-analysis')">
          <el-icon><MagicStick /></el-icon>AI 生成报告
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>手动创建
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="handleSearch">
        <el-form-item label="报告状态">
          <el-select
            v-model="filterForm.status"
            placeholder="全部"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="报告类型">
          <el-select
            v-model="filterForm.report_type"
            placeholder="全部"
            clearable
            style="width: 160px"
            @change="handleSearch"
          >
            <el-option
              v-for="rt in reportTypes"
              :key="rt.value"
              :label="rt.label"
              :value="rt.value"
            />
          </el-select>
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
        empty-text="暂无报告，点击「生成报告」创建"
      >
        <el-table-column prop="title" label="报告标题" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="report-title" @click="openDetail(row)">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="report_type" label="类型" width="130">
          <template #default="{ row }">
            <el-tag v-if="row.report_type" size="small" :type="reportTypeTag(row.report_type)">
              {{ reportTypeLabel(row.report_type) }}
            </el-tag>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="generated_by" label="生成方式" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.generated_by === 'ai' ? 'success' : ''">
              {{ row.generated_by === 'ai' ? 'AI 生成' : row.generated_by === 'scheduled' ? '定时' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" min-width="150">
          <template #default="{ row }">
            <el-tag
              v-for="t in (row.tags || []).slice(0, 3)"
              :key="t"
              size="small"
              class="kw-tag"
            >{{ t }}</el-tag>
            <el-tag v-if="(row.tags || []).length > 3" size="small" class="kw-tag">
              +{{ row.tags.length - 3 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">查看</el-button>
            <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm
              title="确认删除该报告？"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
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

    <!-- 新增/编辑 Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑报告' : '生成报告'"
      width="700px"
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
        <el-form-item label="报告标题" prop="title">
          <el-input v-model="formData.title" placeholder="报告标题" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="报告类型" prop="report_type">
              <el-select
                v-model="formData.report_type"
                placeholder="选择类型"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="rt in reportTypes"
                  :key="rt.value"
                  :label="rt.label"
                  :value="rt.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="formData.status" style="width: 100%">
                <el-option label="草稿" value="draft" />
                <el-option label="进行中" value="in_progress" />
                <el-option label="已完成" value="completed" />
                <el-option label="已归档" value="archived" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="关联情报" prop="intelligence_id">
          <el-select
            v-model="formData.intelligence_id"
            placeholder="选择关联情报（可选）"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="intel in intelOptions"
              :key="intel.id"
              :label="intel.title"
              :value="intel.id"
            />
          </el-select>
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
        <el-form-item label="报告内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="10"
            placeholder="输入报告正文（支持 Markdown 格式）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情 Drawer -->
    <el-drawer
      v-model="detailVisible"
      title="报告详情"
      size="620px"
      destroy-on-close
    >
      <template v-if="detailRow">
        <div class="detail-section">
          <div class="detail-header">
            <h3>{{ detailRow.title }}</h3>
            <div class="detail-meta">
              <el-tag v-if="detailRow.report_type" size="small" :type="reportTypeTag(detailRow.report_type)">
                {{ reportTypeLabel(detailRow.report_type) }}
              </el-tag>
              <el-tag size="small" :type="statusTagType(detailRow.status)">
                {{ statusLabel(detailRow.status) }}
              </el-tag>
              <el-tag size="small" :type="detailRow.generated_by === 'ai' ? 'success' : ''">
                {{ detailRow.generated_by === 'ai' ? 'AI 生成' : detailRow.generated_by === 'scheduled' ? '定时生成' : '手动录入' }}
              </el-tag>
            </div>
          </div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="创建时间">{{ formatDate(detailRow.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatDate(detailRow.updated_at) }}</el-descriptions-item>
            <el-descriptions-item v-if="detailRow.tags?.length" label="标签">
              <el-tag v-for="t in detailRow.tags" :key="t" size="small" class="tag-item">{{ t }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          <div class="detail-content">
            <h4>报告内容</h4>
            <div class="markdown-body" v-html="renderMarkdown(detailRow.content || '')"></div>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { reportApi } from '@/api/reports'
import { intelligenceApi } from '@/api/intelligence'
import { useRouter } from 'vue-router'
import type { Report, ReportCreate } from '@/types'

const router = useRouter()

// ---------- 配置 ----------
const reportTypes = [
  { value: 'competitor_analysis', label: '竞品分析' },
  { value: 'swot', label: 'SWOT分析' },
  { value: 'trend', label: '趋势报告' },
  { value: 'alert', label: '预警报告' },
  { value: 'quarterly', label: '季度报告' },
  { value: 'other', label: '其他' },
]

const reportTypeLabelMap: Record<string, string> = {}
reportTypes.forEach((rt) => { reportTypeLabelMap[rt.value] = rt.label })

const reportTypeTagMap: Record<string, string> = {
  competitor_analysis: 'success',
  swot: 'warning',
  trend: '',
  alert: 'danger',
  quarterly: 'success',
  other: 'info',
}

function reportTypeLabel(t: string) { return reportTypeLabelMap[t] || t }
function reportTypeTag(t: string) { return reportTypeTagMap[t] || '' }

function statusLabel(s: string) {
  const map: Record<string, string> = { draft: '草稿', in_progress: '进行中', completed: '已完成', archived: '已归档' }
  return map[s] || s
}
function statusTagType(s: string) {
  const map: Record<string, string> = { draft: 'info', in_progress: 'warning', completed: 'success', archived: '' }
  return map[s] || ''
}

function formatDate(d: string | null) {
  if (!d) return '--'
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

// ---------- 简单 Markdown 渲染 ----------
function renderMarkdown(content: string) {
  if (!content) return '<p class="text-muted">暂无内容</p>'
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 标题
  html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>')
  // 粗体 / 斜体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  // 行内代码
  html = html.replace(/`(.+?)`/g, '<code>$1</code>')
  // 链接
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>')
  // 无序列表
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
  // 换行
  html = html.replace(/\n\n/g, '</p><p>')
  html = html.replace(/\n/g, '<br>')
  html = '<p>' + html + '</p>'
  // 清理空标签
  html = html.replace(/<p>\s*<\/p>/g, '')
  return html
}

// ---------- 情报选项 ----------
const intelOptions = ref<{ id: string; title: string }[]>([])

async function fetchIntelOptions() {
  try {
    const res = await intelligenceApi.list({ page_size: 100 })
    intelOptions.value = res.data.items.map((i) => ({ id: i.id, title: i.title }))
  } catch {
    // ignore
  }
}

// ---------- 表格数据 ----------
const loading = ref(false)
const tableData = ref<Report[]>([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const filterForm = reactive({
  status: '' as string,
  report_type: '' as string,
})

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (filterForm.status) params.status = filterForm.status
    if (filterForm.report_type) params.report_type = filterForm.report_type

    const res = await reportApi.list(params)
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch {
    ElMessage.error('加载报告列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function resetFilter() {
  filterForm.status = ''
  filterForm.report_type = ''
  handleSearch()
}

// ---------- 详情抽屉 ----------
const detailVisible = ref(false)
const detailRow = ref<Report | null>(null)

function openDetail(row: Report) {
  detailRow.value = row
  detailVisible.value = true
}

// ---------- 弹窗表单 ----------
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref('')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

const defaultForm: ReportCreate = {
  title: '',
  content: '',
  status: 'draft',
  report_type: '',
  intelligence_id: '',
  tags: [],
}

const formData = reactive<ReportCreate>({ ...defaultForm })

const formRules: FormRules = {
  title: [{ required: true, message: '请输入报告标题', trigger: 'blur' }],
}

function openCreateDialog() {
  isEdit.value = false
  editingId.value = ''
  Object.assign(formData, { ...defaultForm, tags: [], intelligence_id: '' })
  dialogVisible.value = true
}

function openEditDialog(row: Report) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(formData, {
    title: row.title,
    content: row.content || '',
    status: row.status,
    report_type: row.report_type || '',
    intelligence_id: row.intelligence_id || '',
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
      await reportApi.update(editingId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await reportApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitLoading.value = false
  }
}

// ---------- 删除 ----------
async function handleDelete(id: string) {
  try {
    await reportApi.remove(id)
    ElMessage.success('已删除')
    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page--
    }
    fetchList()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchList()
  fetchIntelOptions()
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

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card { margin-bottom: 16px; }
.filter-card .el-form { margin-bottom: -8px; }

.report-title {
  font-weight: 500;
  cursor: pointer;
  color: #409eff;
}

.report-title:hover { text-decoration: underline; }

.kw-tag { margin-right: 4px; }
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
  gap: 10px;
  flex-wrap: wrap;
}

.detail-content {
  margin-top: 20px;
}

.detail-content h4 {
  margin: 0 0 12px;
  font-size: 15px;
  color: #303133;
}

.markdown-body {
  padding: 20px;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
}

.markdown-body :deep(h2) { font-size: 18px; margin: 16px 0 10px; }
.markdown-body :deep(h3) { font-size: 16px; margin: 14px 0 8px; }
.markdown-body :deep(h4) { font-size: 14px; margin: 12px 0 6px; }
.markdown-body :deep(p) { margin: 8px 0; }
.markdown-body :deep(ul) { padding-left: 20px; margin: 8px 0; }
.markdown-body :deep(li) { margin: 4px 0; }
.markdown-body :deep(code) {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}
.markdown-body :deep(a) {
  color: #409eff;
  text-decoration: none;
}
.markdown-body :deep(a:hover) { text-decoration: underline; }

.tag-item { margin-right: 6px; }
</style>
