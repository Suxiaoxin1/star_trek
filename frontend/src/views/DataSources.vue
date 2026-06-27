<template>
  <div class="datasources-page">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-num">{{ stats.total }}</div>
          <div class="stat-label">数据源总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card active">
          <div class="stat-num">{{ stats.active }}</div>
          <div class="stat-label">启用数据源</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card inactive">
          <div class="stat-num">{{ stats.inactive }}</div>
          <div class="stat-label">禁用数据源</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card success">
          <div class="stat-num">{{ stats.by_status?.success || 0 }}</div>
          <div class="stat-label">采集成功</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选 + 操作 -->
    <el-card class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="4">
          <el-select v-model="filters.source_type" placeholder="数据源类型" clearable @change="loadList">
            <el-option label="RSS" value="rss" />
            <el-option label="Web 爬虫" value="web_scraper" />
            <el-option label="API" value="api" />
            <el-option label="社交媒体" value="social_media" />
            <el-option label="新闻" value="news" />
            <el-option label="手动" value="manual" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.is_active" placeholder="状态" clearable @change="loadList">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="5">
          <el-input v-model="filters.keyword" placeholder="搜索名称..." clearable @clear="loadList" @keyup.enter="loadList" />
        </el-col>
        <el-col :span="11" style="text-align: right">
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon> 新增数据源
          </el-button>
          <el-button type="success" @click="handleCrawlAll" :loading="crawlAllLoading">
            <el-icon><Refresh /></el-icon> 全量采集
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 数据源列表 -->
    <el-card>
      <el-table :data="sources" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column prop="source_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="typeTagMap[row.source_type]" size="small">
              {{ typeLabelMap[row.source_type] || row.source_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="URL" min-width="250" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="crawl_interval_minutes" label="间隔(分钟)" width="100" />
        <el-table-column prop="last_status" label="采集状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.last_status" :type="row.last_status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.last_status === 'success' ? '成功' : '失败' }}
            </el-tag>
            <span v-else class="text-muted">未采集</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_crawled_at" label="上次采集" width="160">
          <template #default="{ row }">
            {{ row.last_crawled_at ? formatTime(row.last_crawled_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleCrawl(row)" :disabled="!row.is_active">
              采集
            </el-button>
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadList"
        class="pagination"
      />
    </el-card>

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="showCreateDialog" :title="editingSource ? '编辑数据源' : '新增数据源'" width="650px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="数据源名称" />
        </el-form-item>
        <el-form-item label="类型" prop="source_type">
          <el-select v-model="formData.source_type" placeholder="选择类型">
            <el-option label="RSS" value="rss" />
            <el-option label="Web 爬虫" value="web_scraper" />
            <el-option label="API" value="api" />
            <el-option label="社交媒体" value="social_media" />
            <el-option label="新闻" value="news" />
            <el-option label="手动" value="manual" />
          </el-select>
        </el-form-item>
        <el-form-item label="URL" prop="url">
          <el-input v-model="formData.url" placeholder="数据源 URL" />
        </el-form-item>
        <el-form-item label="采集间隔" prop="crawl_interval_minutes">
          <el-input-number v-model="formData.crawl_interval_minutes" :min="10" :step="30" />
          <span class="form-tip">分钟</span>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="formData.is_active" />
        </el-form-item>

        <!-- 爬虫配置 (仅 web_scraper) -->
        <el-divider v-if="formData.source_type === 'web_scraper'" content-position="left">爬虫配置</el-divider>
        <el-form-item v-if="formData.source_type === 'web_scraper'" label="标题选择器">
          <el-input v-model="formData.crawl_config.selectors.title" placeholder="如: h1, .title" />
        </el-form-item>
        <el-form-item v-if="formData.source_type === 'web_scraper'" label="内容选择器">
          <el-input v-model="formData.crawl_config.selectors.content" placeholder="如: article, .content" />
        </el-form-item>
        <el-form-item v-if="formData.source_type === 'web_scraper'" label="链接选择器">
          <el-input v-model="formData.crawl_config.selectors.links" placeholder="如: .post-list a (留空表示单页采集)" />
        </el-form-item>
        <el-form-item v-if="formData.source_type === 'web_scraper'" label="最大页数">
          <el-input-number v-model="formData.crawl_config.max_pages" :min="1" :max="20" />
        </el-form-item>

        <!-- API 配置 (仅 api) -->
        <el-divider v-if="formData.source_type === 'api'" content-position="left">API 配置</el-divider>
        <el-form-item v-if="formData.source_type === 'api'" label="API Endpoint">
          <el-input v-model="formData.api_config.endpoint" placeholder="API 请求地址" />
        </el-form-item>
        <el-form-item v-if="formData.source_type === 'api'" label="数据路径">
          <el-input v-model="formData.api_config.items_path" placeholder="如: data.items" />
        </el-form-item>
        <el-form-item v-if="formData.source_type === 'api'" label="字段映射(JSON)">
          <el-input v-model="apiMappingText" type="textarea" :rows="3" placeholder='{"title":"title","content":"body","url":"link"}' />
        </el-form-item>

        <!-- RSS 配置 -->
        <el-divider v-if="formData.source_type === 'rss'" content-position="left">RSS 配置</el-divider>
        <el-form-item v-if="formData.source_type === 'rss'" label="语言">
          <el-select v-model="formData.crawl_config.language">
            <el-option label="中文" value="zh" />
            <el-option label="英文" value="en" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { datasourceApi } from '@/api/datasources'
import type { DataSource, DataSourceCreate, DataSourceStats } from '@/types'

const loading = ref(false)
const saving = ref(false)
const crawlAllLoading = ref(false)
const sources = ref<DataSource[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const stats = ref<DataSourceStats>({ total: 0, active: 0, inactive: 0, by_type: {}, by_status: {} })

const filters = reactive({
  source_type: '' as string,
  is_active: undefined as boolean | undefined,
  keyword: '' as string,
})

const showCreateDialog = ref(false)
const editingSource = ref<DataSource | null>(null)
const formRef = ref<FormInstance>()

const typeTagMap: Record<string, string> = { rss: 'info', web_scraper: 'warning', api: 'success', social_media: 'danger', news: 'info', manual: 'info' }
const typeLabelMap: Record<string, string> = { rss: 'RSS', web_scraper: 'Web爬虫', api: 'API', social_media: '社交媒体', news: '新闻', manual: '手动' }

const formData = reactive<DataSourceCreate & { crawl_config: any; api_config: any }>({
  name: '',
  source_type: 'rss',
  url: '',
  crawl_interval_minutes: 360,
  is_active: true,
  crawl_config: { selectors: { title: 'h1', content: 'article', links: '' }, max_pages: 1, language: 'zh' },
  api_config: { endpoint: '', items_path: '', field_mapping: {} },
})

const apiMappingText = computed({
  get: () => JSON.stringify(formData.api_config.field_mapping || {}, null, 2),
  set: (v: string) => { try { formData.api_config.field_mapping = JSON.parse(v) } catch {} },
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  source_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  url: [{ required: true, message: '请输入 URL', trigger: 'blur' }],
}

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN')
}

async function loadList() {
  loading.value = true
  try {
    const { data } = await datasourceApi.list({
      ...filters,
      page: page.value,
      page_size: pageSize.value,
    })
    sources.value = data.items
    total.value = data.total
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const { data } = await datasourceApi.stats()
    stats.value = data
  } catch {}
}

function openEdit(row: DataSource) {
  editingSource.value = row
  formData.name = row.name
  formData.source_type = row.source_type
  formData.url = row.url || ''
  formData.crawl_interval_minutes = row.crawl_interval_minutes
  formData.is_active = row.is_active
  formData.crawl_config = row.crawl_config || { selectors: { title: 'h1', content: 'article', links: '' }, max_pages: 1, language: 'zh' }
  formData.api_config = row.api_config || { endpoint: '', items_path: '', field_mapping: {} }
  showCreateDialog.value = true
}

function resetForm() {
  editingSource.value = null
  formData.name = ''
  formData.source_type = 'rss'
  formData.url = ''
  formData.crawl_interval_minutes = 360
  formData.is_active = true
  formData.crawl_config = { selectors: { title: 'h1', content: 'article', links: '' }, max_pages: 1, language: 'zh' }
  formData.api_config = { endpoint: '', items_path: '', field_mapping: {} }
}

async function handleSave() {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editingSource.value) {
      await datasourceApi.update(editingSource.value.id, formData)
      ElMessage.success('更新成功')
    } else {
      await datasourceApi.create(formData)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    resetForm()
    loadList()
    loadStats()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: DataSource) {
  await ElMessageBox.confirm(`确定删除数据源「${row.name}」？关联的采集数据也将被删除。`, '确认删除', { type: 'warning' })
  try {
    await datasourceApi.remove(row.id)
    ElMessage.success('已删除')
    loadList()
    loadStats()
  } catch (e: any) {
    ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleCrawl(row: DataSource) {
  try {
    await datasourceApi.triggerCrawl(row.id)
    ElMessage.success(`已下发采集任务: ${row.name}`)
  } catch (e: any) {
    ElMessage.error('下发失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleCrawlAll() {
  crawlAllLoading.value = true
  try {
    await datasourceApi.triggerCrawlAll()
    ElMessage.success('已下发全量采集任务')
  } catch (e: any) {
    ElMessage.error('下发失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    crawlAllLoading.value = false
  }
}

// 弹窗关闭时重置
watch(showCreateDialog, (v) => { if (!v) resetForm() })

onMounted(() => {
  loadList()
  loadStats()
})
</script>



<style scoped>
.datasources-page { padding: 0; }
.stats-row { margin-bottom: 16px; }
.stat-card { text-align: center; }
.stat-num { font-size: 28px; font-weight: 700; color: #303133; }
.stat-card.active .stat-num { color: #67c23a; }
.stat-card.inactive .stat-num { color: #909399; }
.stat-card.success .stat-num { color: #409eff; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.filter-card { margin-bottom: 16px; }
.pagination { margin-top: 16px; justify-content: center; }
.form-tip { margin-left: 8px; color: #909399; font-size: 13px; }
.text-muted { color: #c0c4cc; }
</style>