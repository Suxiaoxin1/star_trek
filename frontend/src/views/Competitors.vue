<template>
  <div class="page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <h2>竞品管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>新增竞品
      </el-button>
    </div>

    <!-- 搜索筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" @submit.prevent="handleSearch">
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.keyword"
            placeholder="名称 / 英文名搜索"
            clearable
            style="width: 260px"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="竞品层级">
          <el-select
            v-model="filterForm.tier"
            placeholder="全部"
            clearable
            style="width: 140px"
            @change="handleSearch"
          >
            <el-option label="直接竞品" value="direct" />
            <el-option label="间接竞品" value="indirect" />
            <el-option label="潜在竞品" value="potential" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.is_active"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option label="活跃" :value="true" />
            <el-option label="停用" :value="false" />
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
        empty-text="暂无竞品数据，点击「新增竞品」开始添加"
      >
        <el-table-column prop="name" label="名称" min-width="160">
          <template #default="{ row }">
            <div class="cell-name">
              <el-avatar v-if="row.logo_url" :src="row.logo_url" :size="32" />
              <el-avatar v-else :size="32" :style="{ background: avatarColors[row.name?.charCodeAt(0) % 5] }">
                {{ row.name?.charAt(0) }}
              </el-avatar>
              <div class="cell-name-text">
                <span class="name-main">{{ row.name }}</span>
                <span v-if="row.name_en" class="name-sub">{{ row.name_en }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="tier" label="层级" width="110">
          <template #default="{ row }">
            <el-tag :type="tierTagType(row.tier)" size="small">{{ tierLabel(row.tier) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="website" label="官网" min-width="180">
          <template #default="{ row }">
            <a v-if="row.website" :href="row.website" target="_blank" class="link">
              {{ row.website }}
            </a>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="headquarters" label="总部" width="120" show-overflow-tooltip />
        <el-table-column prop="funding_stage" label="融资阶段" width="110">
          <template #default="{ row }">
            <span v-if="row.funding_stage">{{ row.funding_stage }}</span>
            <span v-else class="text-muted">--</span>
          </template>
        </el-table-column>
        <el-table-column prop="product_count" label="产品数" width="85" align="center" sortable />
        <el-table-column prop="intel_count" label="情报数" width="85" align="center" sortable />
        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="goDetail(row.id)">详情</el-button>
            <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-popconfirm
              title="确认停用该竞品？"
              confirm-button-text="确认"
              cancel-button-text="取消"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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
      :title="isEdit ? '编辑竞品' : '新增竞品'"
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
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="竞品中文名称" />
        </el-form-item>
        <el-form-item label="英文名" prop="name_en">
          <el-input v-model="formData.name_en" placeholder="竞品英文名称" />
        </el-form-item>
        <el-form-item label="官网" prop="website">
          <el-input v-model="formData.website" placeholder="https://" />
        </el-form-item>
        <el-form-item label="竞品层级" prop="tier">
          <el-select v-model="formData.tier" placeholder="选择竞品层级" style="width: 100%">
            <el-option label="直接竞品" value="direct" />
            <el-option label="间接竞品" value="indirect" />
            <el-option label="潜在竞品" value="potential" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="简要描述该竞品" />
        </el-form-item>
        <el-form-item label="总部" prop="headquarters">
          <el-input v-model="formData.headquarters" placeholder="城市/国家" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="成立年份" prop="founded_year">
              <el-input-number v-model="formData.founded_year" :min="1900" :max="2099" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="员工规模" prop="employee_count">
              <el-input v-model="formData.employee_count" placeholder="如: 100-500" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="融资阶段" prop="funding_stage">
              <el-select v-model="formData.funding_stage" placeholder="选择阶段" style="width: 100%" clearable>
                <el-option label="天使轮" value="天使轮" />
                <el-option label="A轮" value="A轮" />
                <el-option label="B轮" value="B轮" />
                <el-option label="C轮" value="C轮" />
                <el-option label="D轮+" value="D轮+" />
                <el-option label="IPO" value="IPO" />
                <el-option label="未融资" value="未融资" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="融资总额" prop="total_funding">
              <el-input v-model="formData.total_funding" placeholder="如: $50M" />
            </el-form-item>
          </el-col>
        </el-row>
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
        <el-form-item label="启用" prop="is_active">
          <el-switch v-model="formData.is_active" />
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { competitorApi } from '@/api/competitors'
import type { Competitor, CompetitorCreate } from '@/types'

const router = useRouter()

// ---------- 表格数据 ----------
const loading = ref(false)
const tableData = ref<Competitor[]>([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

// ---------- 筛选 ----------
const filterForm = reactive({
  keyword: '',
  tier: '' as string,
  is_active: undefined as boolean | undefined,
})

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (filterForm.keyword) params.keyword = filterForm.keyword
    if (filterForm.tier) params.tier = filterForm.tier
    if (filterForm.is_active !== undefined) params.is_active = filterForm.is_active

    const res = await competitorApi.list(params as any)
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch {
    ElMessage.error('加载竞品列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function resetFilter() {
  filterForm.keyword = ''
  filterForm.tier = ''
  filterForm.is_active = undefined
  handleSearch()
}

// ---------- 层级标签 ----------
const tierLabelMap: Record<string, string> = { direct: '直接竞品', indirect: '间接竞品', potential: '潜在竞品' }
const tierTagMap: Record<string, string> = { direct: 'danger', indirect: 'warning', potential: '' }

function tierLabel(tier: string) {
  return tierLabelMap[tier] || tier
}
function tierTagType(tier: string) {
  return tierTagMap[tier] || 'info'
}

// ---------- 头像颜色 ----------
const avatarColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']

// ---------- 弹窗表单 ----------
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref('')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

const defaultForm: CompetitorCreate = {
  name: '',
  name_en: '',
  website: '',
  tier: 'direct',
  description: '',
  headquarters: '',
  founded_year: undefined,
  employee_count: '',
  funding_stage: '',
  total_funding: '',
  tags: [],
  is_active: true,
}

const formData = reactive<CompetitorCreate>({ ...defaultForm })

const formRules: FormRules = {
  name: [{ required: true, message: '请输入竞品名称', trigger: 'blur' }],
}

function openCreateDialog() {
  isEdit.value = false
  editingId.value = ''
  Object.assign(formData, { ...defaultForm, tags: [] })
  dialogVisible.value = true
}

function openEditDialog(row: Competitor) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name,
    name_en: row.name_en || '',
    website: row.website || '',
    tier: row.tier,
    description: row.description || '',
    headquarters: row.headquarters || '',
    founded_year: row.founded_year || undefined,
    employee_count: row.employee_count || '',
    funding_stage: row.funding_stage || '',
    total_funding: row.total_funding || '',
    tags: row.tags ? [...row.tags] : [],
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await competitorApi.update(editingId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await competitorApi.create(formData)
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
    await competitorApi.remove(id)
    ElMessage.success('已删除')
    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page--
    }
    fetchList()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ---------- 跳转详情 ----------
function goDetail(id: string) {
  router.push(`/competitors/${id}`)
}

onMounted(() => {
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

.filter-card { margin-bottom: 16px; }
.filter-card .el-form { margin-bottom: -8px; }

.cell-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cell-name-text {
  display: flex;
  flex-direction: column;
}

.name-main { font-weight: 500; }
.name-sub { font-size: 12px; color: #909399; margin-top: 2px; }

.link {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.link:hover { text-decoration: underline; }
.text-muted { color: #c0c4cc; }

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
