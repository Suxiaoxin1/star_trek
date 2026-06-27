<template>
  <div class="page">
    <div class="page-header">
      <h2>预警中心</h2>
      <p class="page-desc">配置预警规则，及时发现竞品重大动态</p>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card stat-unread">
          <div class="stat-num">{{ alertStats.unread_alerts }}</div>
          <div class="stat-label">未读预警</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card stat-unresolved">
          <div class="stat-num">{{ alertStats.unresolved_alerts }}</div>
          <div class="stat-label">待处理预警</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card stat-rules">
          <div class="stat-num">{{ alertStats.active_rules }}</div>
          <div class="stat-label">活跃规则</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Tab 切换 -->
    <el-card class="main-card">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <!-- ==================== 预警规则 ==================== -->
        <el-tab-pane label="预警规则" name="rules">
          <template #label>
            <span><el-icon><Setting /></el-icon> 预警规则</span>
          </template>

          <div class="tab-header">
            <el-select
              v-model="ruleFilterActive"
              placeholder="规则状态"
              clearable
              style="width: 140px"
              @change="fetchRules"
            >
              <el-option label="全部" value="" />
              <el-option label="已启用" value="true" />
              <el-option label="已停用" value="false" />
            </el-select>
            <el-button type="primary" @click="openRuleDialog()">
              <el-icon><Plus /></el-icon>新增规则
            </el-button>
          </div>

          <el-table
            v-loading="rulesLoading"
            :data="rulesData"
            stripe
            empty-text="暂无预警规则"
          >
            <el-table-column prop="name" label="规则名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.description || '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="target_type" label="监控类型" width="110">
              <template #default="{ row }">
                <el-tag v-if="row.target_type" size="small">{{ targetTypeLabel(row.target_type) }}</el-tag>
                <span v-else class="text-muted">--</span>
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="严重程度" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="severityTagType(row.severity)">
                  {{ severityLabel(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="keywords" label="关键词" min-width="150">
              <template #default="{ row }">
                <el-tag
                  v-for="kw in (row.keywords || []).slice(0, 3)"
                  :key="kw"
                  size="small"
                  class="kw-tag"
                >{{ kw }}</el-tag>
                <el-tag v-if="(row.keywords || []).length > 3" size="small" class="kw-tag">
                  +{{ row.keywords.length - 3 }}
                </el-tag>
                <span v-if="!row.keywords?.length" class="text-muted">--</span>
              </template>
            </el-table-column>
            <el-table-column prop="notification_channels" label="通知渠道" width="140">
              <template #default="{ row }">
                <el-tag
                  v-for="ch in (row.notification_channels || [])"
                  :key="ch"
                  size="small"
                  class="kw-tag"
                >{{ channelLabel(ch) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-switch
                  :model-value="row.is_active"
                  size="small"
                  @change="(val: boolean) => toggleRule(row.id, val)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openRuleDialog(row)">编辑</el-button>
                <el-popconfirm
                  title="确认删除该规则？"
                  @confirm="handleDeleteRule(row.id)"
                >
                  <template #reference>
                    <el-button link type="danger" size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- ==================== 预警历史 ==================== -->
        <el-tab-pane label="预警历史" name="history">
          <template #label>
            <span>
              <el-icon><Bell /></el-icon> 预警历史
              <el-badge
                v-if="alertStats.unread_alerts > 0"
                :value="alertStats.unread_alerts"
                class="tab-badge"
              />
            </span>
          </template>

          <div class="tab-header">
            <el-select
              v-model="historyFilter.severity"
              placeholder="严重程度"
              clearable
              style="width: 130px"
              @change="fetchHistory"
            >
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="严重" value="critical" />
            </el-select>
            <el-select
              v-model="historyFilter.is_read"
              placeholder="阅读状态"
              clearable
              style="width: 130px"
              @change="fetchHistory"
            >
              <el-option label="未读" :value="false" />
              <el-option label="已读" :value="true" />
            </el-select>
            <el-select
              v-model="historyFilter.rule_id"
              placeholder="关联规则"
              clearable
              filterable
              style="width: 200px"
              @change="fetchHistory"
            >
              <el-option
                v-for="r in rulesData"
                :key="r.id"
                :label="r.name"
                :value="r.id"
              />
            </el-select>
          </div>

          <el-table
            v-loading="historyLoading"
            :data="historyData"
            stripe
            empty-text="暂无预警记录"
          >
            <el-table-column prop="severity" label="级别" width="85" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="severityTagType(row.severity)">
                  {{ severityLabel(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="预警标题" min-width="220" show-overflow-tooltip>
              <template #default="{ row }">
                <span :class="{ 'unread-row': !row.is_read }">{{ row.title }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="rule_name" label="触发规则" width="150" show-overflow-tooltip />
            <el-table-column prop="is_read" label="状态" width="110" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.is_read ? 'info' : 'warning'">
                  {{ row.is_read ? '已读' : '未读' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_resolved" label="处理" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.is_resolved ? 'success' : 'danger'">
                  {{ row.is_resolved ? '已处理' : '待处理' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="triggered_at" label="触发时间" width="170">
              <template #default="{ row }">
                {{ formatDate(row.triggered_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="!row.is_read"
                  link
                  type="primary"
                  size="small"
                  @click="handleMarkRead(row.id)"
                >标记已读</el-button>
                <el-button
                  v-if="!row.is_resolved"
                  link
                  type="success"
                  size="small"
                  @click="handleResolve(row.id)"
                >处理</el-button>
                <el-button
                  v-if="row.content"
                  link
                  type="primary"
                  size="small"
                  @click="showContent(row)"
                >查看</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="historyPagination.page"
              v-model:page-size="historyPagination.page_size"
              :total="historyPagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              @current-change="fetchHistory"
              @size-change="fetchHistory"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 规则 Dialog -->
    <el-dialog
      v-model="ruleDialogVisible"
      :title="isRuleEdit ? '编辑预警规则' : '新增预警规则'"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="ruleFormRef"
        :model="ruleFormData"
        :rules="ruleFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="ruleFormData.name" placeholder="预警规则名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="ruleFormData.description"
            type="textarea"
            :rows="2"
            placeholder="规则描述（可选）"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="监控类型" prop="target_type">
              <el-select
                v-model="ruleFormData.target_type"
                placeholder="选择类型"
                clearable
                style="width: 100%"
              >
                <el-option label="竞品" value="competitor" />
                <el-option label="产品" value="product" />
                <el-option label="关键词" value="keyword" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="严重程度" prop="severity">
              <el-select
                v-model="ruleFormData.severity"
                placeholder="选择程度"
                style="width: 100%"
              >
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="严重" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="关键词" prop="keywords">
          <el-select
            v-model="ruleFormData.keywords"
            multiple
            filterable
            allow-create
            placeholder="输入关键词后回车"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="通知渠道" prop="notification_channels">
          <el-checkbox-group v-model="ruleFormData.notification_channels">
            <el-checkbox label="email">邮件</el-checkbox>
            <el-checkbox label="slack">Slack</el-checkbox>
            <el-checkbox label="wechat">微信</el-checkbox>
            <el-checkbox label="webhook">Webhook</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="启用" prop="is_active">
          <el-switch v-model="ruleFormData.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="ruleSubmitLoading" @click="handleRuleSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 预警内容 Dialog -->
    <el-dialog v-model="contentDialogVisible" title="预警详情" width="500px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="标题">{{ contentRow?.title }}</el-descriptions-item>
        <el-descriptions-item label="触发规则">{{ contentRow?.rule_name }}</el-descriptions-item>
        <el-descriptions-item label="严重程度">
          <el-tag size="small" :type="severityTagType(contentRow?.severity)">
            {{ severityLabel(contentRow?.severity) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="触发时间">{{ formatDate(contentRow?.triggered_at) }}</el-descriptions-item>
      </el-descriptions>
      <div v-if="contentRow?.content" class="content-block">
        <h4>预警内容</h4>
        <p>{{ contentRow.content }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Setting, Bell } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { alertApi } from '@/api/alerts'
import type { AlertRule, AlertRuleCreate, AlertHistory } from '@/types'

const activeTab = ref('rules')

// ---------- 统计 ----------
const alertStats = reactive({
  unread_alerts: 0,
  unresolved_alerts: 0,
  active_rules: 0,
})

async function fetchStats() {
  try {
    const res = await alertApi.stats()
    Object.assign(alertStats, res.data)
  } catch {
    // ignore
  }
}

// ---------- 标签映射 ----------
function severityLabel(s: string | null) {
  const map: Record<string, string> = { low: '低', medium: '中', high: '高', critical: '严重' }
  return map[s || ''] || s || '--'
}
function severityTagType(s: string | null) {
  const map: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return map[s || ''] || ''
}
function targetTypeLabel(t: string) {
  const map: Record<string, string> = { competitor: '竞品', product: '产品', keyword: '关键词' }
  return map[t] || t
}
function channelLabel(ch: string) {
  const map: Record<string, string> = { email: '邮件', slack: 'Slack', wechat: '微信', webhook: 'Webhook' }
  return map[ch] || ch
}
function formatDate(d: string | null) {
  if (!d) return '--'
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

// ==================== 预警规则 ====================
const rulesLoading = ref(false)
const rulesData = ref<AlertRule[]>([])
const ruleFilterActive = ref<string>('')

async function fetchRules() {
  rulesLoading.value = true
  try {
    const active = ruleFilterActive.value === '' ? undefined : ruleFilterActive.value === 'true'
    const res = await alertApi.listRules(active)
    rulesData.value = res.data.items
  } catch {
    ElMessage.error('加载规则列表失败')
  } finally {
    rulesLoading.value = false
  }
}

async function toggleRule(id: string, active: boolean) {
  try {
    const rule = rulesData.value.find((r) => r.id === id)
    if (!rule) return
    await alertApi.updateRule(id, {
      name: rule.name,
      description: rule.description || '',
      target_type: rule.target_type || '',
      keywords: rule.keywords || [],
      severity: rule.severity,
      notification_channels: rule.notification_channels || ['email'],
      is_active: active,
    })
    ElMessage.success(active ? '已启用' : '已停用')
    fetchRules()
    fetchStats()
  } catch {
    ElMessage.error('操作失败')
  }
}

// 规则弹窗
const ruleDialogVisible = ref(false)
const isRuleEdit = ref(false)
const editingRuleId = ref('')
const ruleSubmitLoading = ref(false)
const ruleFormRef = ref<FormInstance>()

const defaultRuleForm: AlertRuleCreate = {
  name: '',
  description: '',
  target_type: '',
  severity: 'medium',
  keywords: [],
  notification_channels: ['email'],
  is_active: true,
}

const ruleFormData = reactive<AlertRuleCreate>({ ...defaultRuleForm })

const ruleFormRules: FormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
}

function openRuleDialog(row?: AlertRule) {
  if (row) {
    isRuleEdit.value = true
    editingRuleId.value = row.id
    Object.assign(ruleFormData, {
      name: row.name,
      description: row.description || '',
      target_type: row.target_type || '',
      severity: row.severity,
      keywords: row.keywords ? [...row.keywords] : [],
      notification_channels: row.notification_channels ? [...row.notification_channels] : ['email'],
      is_active: row.is_active,
    })
  } else {
    isRuleEdit.value = false
    editingRuleId.value = ''
    Object.assign(ruleFormData, { ...defaultRuleForm, keywords: [], notification_channels: ['email'] })
  }
  ruleDialogVisible.value = true
}

async function handleRuleSubmit() {
  const valid = await ruleFormRef.value?.validate().catch(() => false)
  if (!valid) return

  ruleSubmitLoading.value = true
  try {
    if (isRuleEdit.value) {
      await alertApi.updateRule(editingRuleId.value, ruleFormData)
      ElMessage.success('更新成功')
    } else {
      await alertApi.createRule(ruleFormData)
      ElMessage.success('创建成功')
    }
    ruleDialogVisible.value = false
    fetchRules()
    fetchStats()
  } catch {
    ElMessage.error(isRuleEdit.value ? '更新失败' : '创建失败')
  } finally {
    ruleSubmitLoading.value = false
  }
}

async function handleDeleteRule(id: string) {
  try {
    await alertApi.deleteRule(id)
    ElMessage.success('已删除')
    fetchRules()
    fetchStats()
  } catch {
    ElMessage.error('删除失败')
  }
}

// ==================== 预警历史 ====================
const historyLoading = ref(false)
const historyData = ref<AlertHistory[]>([])
const historyPagination = reactive({ page: 1, page_size: 20, total: 0 })

const historyFilter = reactive({
  rule_id: '' as string,
  is_read: undefined as boolean | undefined,
  severity: '' as string,
})

async function fetchHistory() {
  historyLoading.value = true
  try {
    const params: Record<string, unknown> = {
      page: historyPagination.page,
      page_size: historyPagination.page_size,
    }
    if (historyFilter.rule_id) params.rule_id = historyFilter.rule_id
    if (historyFilter.is_read !== undefined) params.is_read = historyFilter.is_read
    if (historyFilter.severity) params.severity = historyFilter.severity

    const res = await alertApi.listHistory(params)
    historyData.value = res.data.items
    historyPagination.total = res.data.total
  } catch {
    ElMessage.error('加载预警历史失败')
  } finally {
    historyLoading.value = false
  }
}

async function handleMarkRead(id: string) {
  try {
    await alertApi.markRead(id)
    ElMessage.success('已标记为已读')
    fetchHistory()
    fetchStats()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleResolve(id: string) {
  try {
    await alertApi.resolveAlert(id)
    ElMessage.success('预警已处理')
    fetchHistory()
    fetchStats()
  } catch {
    ElMessage.error('操作失败')
  }
}

// 查看内容
const contentDialogVisible = ref(false)
const contentRow = ref<AlertHistory | null>(null)

function showContent(row: AlertHistory) {
  contentRow.value = row
  contentDialogVisible.value = true
}

// ---------- Tab 切换 ----------
function onTabChange(tab: string) {
  if (tab === 'rules') {
    fetchRules()
  } else {
    fetchRules() // ensure rule options
    fetchHistory()
  }
}

onMounted(() => {
  fetchStats()
  fetchRules()
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

/* 统计卡片 */
.stats-row { margin-bottom: 16px; }

.stat-card { text-align: center; }
.stat-card :deep(.el-card__body) { padding: 18px 12px; }

.stat-num {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-unread .stat-num { color: #e6a23c; }
.stat-unresolved .stat-num { color: #f56c6c; }
.stat-rules .stat-num { color: #409eff; }

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 6px;
}

/* 主卡片 */
.main-card { margin-bottom: 16px; }

/* Tab 头部 */
.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tab-badge {
  margin-left: 8px;
}

/* 表格 */
.unread-row {
  font-weight: 600;
  color: #303133;
}

.kw-tag {
  margin-right: 4px;
  margin-bottom: 2px;
}

.text-muted { color: #c0c4cc; }

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 内容弹窗 */
.content-block {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.content-block h4 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #606266;
}

.content-block p {
  margin: 0;
  font-size: 14px;
  color: #303133;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>
