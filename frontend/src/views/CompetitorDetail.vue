<template>
  <div class="page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="$router.push('/competitors')">
          <el-icon><ArrowLeft /></el-icon>返回列表
        </el-button>
        <h2 v-if="competitor">{{ competitor.name }}</h2>
        <el-skeleton v-else style="width: 200px" :rows="1" animated />
      </div>
      <div v-if="competitor" class="header-actions">
        <el-button type="success" @click="handleAICompetitorAnalysis" :loading="aiCompetitorLoading">
          <el-icon><MagicStick /></el-icon>AI 分析
        </el-button>
        <el-button :type="editing ? 'default' : 'primary'" @click="toggleEdit">
          {{ editing ? '取消编辑' : '编辑信息' }}
        </el-button>
        <el-button v-if="editing" type="primary" :loading="saving" @click="saveBasicInfo">保存</el-button>
      </div>
    </div>

    <el-skeleton v-if="!competitor" :rows="8" animated />

    <template v-else>
      <!-- 基本信息卡片 -->
      <el-card class="info-card">
        <div class="info-header">
          <el-avatar v-if="competitor.logo_url" :src="competitor.logo_url" :size="56" />
          <el-avatar v-else :size="56" :style="{ background: '#409eff' }">
            {{ competitor.name?.charAt(0) }}
          </el-avatar>
          <div class="info-meta">
            <h3>{{ competitor.name }}</h3>
            <p v-if="competitor.name_en">{{ competitor.name_en }}</p>
            <div class="info-tags">
              <el-tag :type="tierTagType(competitor.tier)" size="small">{{ tierLabel(competitor.tier) }}</el-tag>
              <el-tag :type="competitor.is_active ? 'success' : 'info'" size="small">
                {{ competitor.is_active ? '活跃' : '停用' }}
              </el-tag>
              <el-tag v-if="competitor.funding_stage" size="small" type="warning">
                {{ competitor.funding_stage }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Tab 切换 -->
      <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- ============ Tab 1: 基本信息 ============ -->
        <el-tab-pane label="基本信息" name="basic">
          <el-card>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="官网">
                <template v-if="editing">
                  <el-input v-model="editForm.website" placeholder="https://" size="small" />
                </template>
                <a v-else-if="competitor.website" :href="competitor.website" target="_blank" class="link">
                  {{ competitor.website }}
                </a>
                <span v-else class="text-muted">--</span>
              </el-descriptions-item>
              <el-descriptions-item label="总部">
                <template v-if="editing">
                  <el-input v-model="editForm.headquarters" placeholder="城市/国家" size="small" />
                </template>
                <span v-else>{{ competitor.headquarters || '--' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="成立年份">
                <template v-if="editing">
                  <el-input-number v-model="editForm.founded_year" :min="1900" :max="2099" size="small" style="width:100%" />
                </template>
                <span v-else>{{ competitor.founded_year || '--' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="员工规模">
                <template v-if="editing">
                  <el-input v-model="editForm.employee_count" placeholder="如: 100-500" size="small" />
                </template>
                <span v-else>{{ competitor.employee_count || '--' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="融资阶段">
                <template v-if="editing">
                  <el-select v-model="editForm.funding_stage" size="small" style="width:100%" clearable>
                    <el-option label="天使轮" value="天使轮" />
                    <el-option label="A轮" value="A轮" />
                    <el-option label="B轮" value="B轮" />
                    <el-option label="C轮" value="C轮" />
                    <el-option label="D轮+" value="D轮+" />
                    <el-option label="IPO" value="IPO" />
                    <el-option label="未融资" value="未融资" />
                  </el-select>
                </template>
                <span v-else>{{ competitor.funding_stage || '--' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="融资总额">
                <template v-if="editing">
                  <el-input v-model="editForm.total_funding" placeholder="如: $50M" size="small" />
                </template>
                <span v-else>{{ competitor.total_funding || '--' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="竞品层级">
                <template v-if="editing">
                  <el-select v-model="editForm.tier" size="small" style="width:100%">
                    <el-option label="直接竞品" value="direct" />
                    <el-option label="间接竞品" value="indirect" />
                    <el-option label="潜在竞品" value="potential" />
                  </el-select>
                </template>
                <el-tag v-else :type="tierTagType(competitor.tier)" size="small">{{ tierLabel(competitor.tier) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="启用状态">
                <template v-if="editing">
                  <el-switch v-model="editForm.is_active" size="small" />
                </template>
                <el-tag v-else :type="competitor.is_active ? 'success' : 'info'" size="small">
                  {{ competitor.is_active ? '活跃' : '停用' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="标签" :span="2">
                <template v-if="editing">
                  <el-select
                    v-model="editForm.tags"
                    multiple
                    filterable
                    allow-create
                    placeholder="输入标签后回车"
                    size="small"
                    style="width:100%"
                  />
                </template>
                <div v-else>
                  <el-tag v-for="tag in (competitor.tags || [])" :key="tag" size="small" class="tag-item">{{ tag }}</el-tag>
                  <span v-if="!competitor.tags?.length" class="text-muted">--</span>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">
                <template v-if="editing">
                  <el-input v-model="editForm.description" type="textarea" :rows="3" size="small" />
                </template>
                <span v-else>{{ competitor.description || '--' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatDate(competitor.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatDate(competitor.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-tab-pane>

        <!-- ============ Tab 2: 产品列表 ============ -->
        <el-tab-pane label="产品列表" name="products">
          <el-card>
            <div class="tab-header">
              <span class="tab-title">产品 ({{ products.length }})</span>
              <el-button type="primary" size="small" @click="openProductDialog()">
                <el-icon><Plus /></el-icon>新增产品
              </el-button>
            </div>
            <el-table :data="products" v-loading="loadingProducts" stripe empty-text="暂无产品">
              <el-table-column prop="name" label="产品名称" min-width="140" />
              <el-table-column prop="category" label="分类" width="120">
                <template #default="{ row }">
                  <el-tag v-if="row.category" size="small">{{ row.category }}</el-tag>
                  <span v-else class="text-muted">--</span>
                </template>
              </el-table-column>
              <el-table-column prop="pricing_model" label="定价模式" width="110">
                <template #default="{ row }">{{ row.pricing_model || '--' }}</template>
              </el-table-column>
              <el-table-column prop="target_market" label="目标市场" width="120">
                <template #default="{ row }">{{ row.target_market || '--' }}</template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
              <el-table-column prop="is_active" label="状态" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                    {{ row.is_active ? '活跃' : '停用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button link type="primary" size="small" @click="openProductDialog(row)">编辑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <!-- ============ Tab 3: 功能对比 ============ -->
        <el-tab-pane label="功能对比" name="features">
          <el-card>
            <div class="tab-header">
              <span class="tab-title">功能清单</span>
              <el-button type="primary" size="small" @click="openFeatureDialog()">
                <el-icon><Plus /></el-icon>新增功能
              </el-button>
            </div>
            <div v-if="featureCategories.length === 0" class="empty-block">
              <el-empty description="暂无功能记录" :image-size="80" />
            </div>
            <div v-else>
              <div v-for="cat in featureCategories" :key="cat" class="feature-group">
                <h4 class="feature-category">{{ cat }}</h4>
                <el-table :data="featureMap[cat]" size="small" border stripe>
                  <el-table-column prop="feature_name" label="功能名称" min-width="160" />
                  <el-table-column prop="support_level" label="支持程度" width="120" align="center">
                    <template #default="{ row }">
                      <el-tag :type="supportTag(row.support_level)" size="small">
                        {{ supportLabel(row.support_level) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip>
                    <template #default="{ row }">{{ row.description || '--' }}</template>
                  </el-table-column>
                  <el-table-column prop="source_url" label="来源" width="80" align="center">
                    <template #default="{ row }">
                      <a v-if="row.source_url" :href="row.source_url" target="_blank" class="link">链接</a>
                      <span v-else>--</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="80" align="center">
                    <template #default="{ row }">
                      <el-button link type="primary" size="small" @click="openFeatureDialog(row)">编辑</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-card>
        </el-tab-pane>

        <!-- ============ Tab 4: 价格历史 ============ -->
        <el-tab-pane label="价格历史" name="pricing">
          <el-card>
            <div class="tab-header">
              <span class="tab-title">价格变动记录</span>
              <el-button type="primary" size="small" @click="openPricingDialog()">
                <el-icon><Plus /></el-icon>记录价格
              </el-button>
            </div>
            <el-table :data="pricingList" v-loading="loadingPricing" stripe empty-text="暂无价格记录">
              <el-table-column prop="plan_name" label="套餐名称" min-width="130" />
              <el-table-column prop="change_type" label="变动类型" width="100">
                <template #default="{ row }">
                  <el-tag v-if="row.change_type" :type="pricingChangeTag(row.change_type)" size="small">
                    {{ row.change_type }}
                  </el-tag>
                  <span v-else>--</span>
                </template>
              </el-table-column>
              <el-table-column label="旧价格" width="110" align="right">
                <template #default="{ row }">
                  <span v-if="row.old_price != null">{{ formatPrice(row.old_price, row.currency) }}</span>
                  <span v-else class="text-muted">--</span>
                </template>
              </el-table-column>
              <el-table-column label="新价格" width="110" align="right">
                <template #default="{ row }">
                  <span class="price-new">{{ formatPrice(row.new_price, row.currency) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="billing_cycle" label="计费周期" width="100">
                <template #default="{ row }">{{ row.billing_cycle || '--' }}</template>
              </el-table-column>
              <el-table-column prop="change_description" label="说明" min-width="180" show-overflow-tooltip />
              <el-table-column prop="detected_at" label="发现时间" width="170">
                <template #default="{ row }">{{ formatDate(row.detected_at) }}</template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </template>

    <!-- ============ 产品 Dialog ============ -->
    <el-dialog
      v-model="productDialogVisible"
      :title="productEditId ? '编辑产品' : '新增产品'"
      width="520px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form ref="productFormRef" :model="productForm" :rules="productRules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="productForm.name" placeholder="产品名称" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="productForm.category" placeholder="如: SaaS / PaaS" />
        </el-form-item>
        <el-form-item label="定价模式">
          <el-select v-model="productForm.pricing_model" style="width:100%" clearable>
            <el-option label="免费" value="免费" />
            <el-option label="Freemium" value="Freemium" />
            <el-option label="订阅制" value="订阅制" />
            <el-option label="按量付费" value="按量付费" />
            <el-option label="一次性" value="一次性" />
            <el-option label="企业定制" value="企业定制" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标市场">
          <el-input v-model="productForm.target_market" placeholder="目标用户群体" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="productForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="发布日">
          <el-date-picker v-model="productForm.launch_date" type="date" placeholder="选择日期" style="width:100%" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="productForm.tags" multiple filterable allow-create placeholder="输入标签" style="width:100%" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="productForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="productDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="productSaving" @click="saveProduct">确认</el-button>
      </template>
    </el-dialog>

    <!-- ============ 功能 Dialog ============ -->
    <el-dialog
      v-model="featureDialogVisible"
      :title="featureEditId ? '编辑功能' : '新增功能'"
      width="500px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form ref="featureFormRef" :model="featureForm" :rules="featureRules" label-width="90px">
        <el-form-item label="功能分类" prop="category">
          <el-select v-model="featureForm.category" filterable allow-create placeholder="输入或选择分类" style="width:100%">
            <el-option v-for="cat in featureCategories" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="功能名称" prop="feature_name">
          <el-input v-model="featureForm.feature_name" placeholder="功能名称" />
        </el-form-item>
        <el-form-item label="支持程度" prop="support_level">
          <el-select v-model="featureForm.support_level" style="width:100%">
            <el-option label="完全支持" value="full" />
            <el-option label="部分支持" value="partial" />
            <el-option label="不支持" value="none" />
            <el-option label="未知" value="unknown" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="featureForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="来源链接">
          <el-input v-model="featureForm.source_url" placeholder="https://" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="featureDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="featureSaving" @click="saveFeature">确认</el-button>
      </template>
    </el-dialog>

    <!-- ============ AI 分析结果 Dialog ============ -->
    <el-dialog
      v-model="aiResultDialogVisible"
      title="AI 竞品深度分析"
      width="720px"
      destroy-on-close
    >
      <template v-if="aiResult">
        <h3>{{ aiResult.competitor_name }} 深度分析</h3>
        <el-descriptions :column="2" border style="margin-bottom: 16px">
          <el-descriptions-item label="市场定位">{{ aiResult.market_position }}</el-descriptions-item>
          <el-descriptions-item label="威胁等级">
            <el-tag :type="aiResult.threat_level === 'high' ? 'danger' : aiResult.threat_level === 'medium' ? 'warning' : 'info'">
              {{ aiResult.threat_level === 'high' ? '高威胁' : aiResult.threat_level === 'medium' ? '中威胁' : '低威胁' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card shadow="never" style="border-left: 3px solid #67c23a">
              <h4 style="margin:0 0 8px;color:#67c23a">核心优势</h4>
              <ul style="padding-left:16px;margin:0"><li v-for="s in aiResult.strengths" :key="s">{{ s }}</li></ul>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" style="border-left: 3px solid #f56c6c">
              <h4 style="margin:0 0 8px;color:#f56c6c">主要劣势</h4>
              <ul style="padding-left:16px;margin:0"><li v-for="w in aiResult.weaknesses" :key="w">{{ w }}</li></ul>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" style="margin-top:12px">
          <el-col :span="8">
            <el-card shadow="never">
              <h4 style="margin:0 0 8px;color:#409eff">我方机会</h4>
              <ul style="padding-left:16px;margin:0"><li v-for="o in aiResult.opportunity_for_us" :key="o">{{ o }}</li></ul>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never">
              <h4 style="margin:0 0 8px;color:#e6a23c">策略建议</h4>
              <ul style="padding-left:16px;margin:0"><li v-for="r in aiResult.strategic_recommendations" :key="r">{{ r }}</li></ul>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never">
              <h4 style="margin:0 0 8px;color:#f56c6c">风险因素</h4>
              <ul style="padding-left:16px;margin:0"><li v-for="r in aiResult.risk_factors" :key="r">{{ r }}</li></ul>
            </el-card>
          </el-col>
        </el-row>
        <el-card v-if="aiResult.recent_highlights?.length" shadow="never" style="margin-top:12px">
          <h4 style="margin:0 0 8px">近期重要动向</h4>
          <ul style="padding-left:16px;margin:0"><li v-for="h in aiResult.recent_highlights" :key="h">{{ h }}</li></ul>
        </el-card>
      </template>
      <template #footer>
        <el-button @click="aiResultDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ============ 价格 Dialog ============ -->
    <el-dialog
      v-model="pricingDialogVisible"
      title="记录价格变动"
      width="520px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form ref="pricingFormRef" :model="pricingForm" :rules="pricingRules" label-width="90px">
        <el-form-item label="套餐名称" prop="plan_name">
          <el-input v-model="pricingForm.plan_name" placeholder="如: 企业版" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="旧价格">
              <el-input-number v-model="pricingForm.old_price" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="新价格" prop="new_price">
              <el-input-number v-model="pricingForm.new_price" :min="0" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="币种">
              <el-select v-model="pricingForm.currency" style="width:100%">
                <el-option label="CNY (¥)" value="CNY" />
                <el-option label="USD ($)" value="USD" />
                <el-option label="EUR (€)" value="EUR" />
                <el-option label="JPY (¥)" value="JPY" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="计费周期">
              <el-select v-model="pricingForm.billing_cycle" style="width:100%" clearable>
                <el-option label="按月" value="月" />
                <el-option label="按年" value="年" />
                <el-option label="一次性" value="一次性" />
                <el-option label="按量" value="按量" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="变动类型">
          <el-select v-model="pricingForm.change_type" style="width:100%" clearable>
            <el-option label="新发布" value="新发布" />
            <el-option label="涨价" value="涨价" />
            <el-option label="降价" value="降价" />
            <el-option label="套餐调整" value="套餐调整" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="pricingForm.change_description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="发现时间" prop="detected_at">
          <el-date-picker
            v-model="pricingForm.detected_at"
            type="datetime"
            placeholder="选择时间"
            style="width:100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pricingDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pricingSaving" @click="savePricing">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { competitorApi } from '@/api/competitors'
import { aiApi } from '@/api/ai'
import type { Competitor, Product, Feature, PricingEntry, CompetitorUpdate, AICompetitorResult } from '@/types'

const route = useRoute()
const router = useRouter()

// ---------- 竞品详情 ----------
const competitor = ref<Competitor | null>(null)
const editing = ref(false)
const saving = ref(false)

const editForm = reactive<CompetitorUpdate>({})

const tierLabelMap: Record<string, string> = { direct: '直接竞品', indirect: '间接竞品', potential: '潜在竞品' }
const tierTagMap: Record<string, string> = { direct: 'danger', indirect: 'warning', potential: '' }
function tierLabel(t: string) { return tierLabelMap[t] || t }
function tierTagType(t: string) { return tierTagMap[t] || 'info' }

async function fetchDetail() {
  const id = route.params.id as string
  try {
    const res = await competitorApi.get(id)
    competitor.value = res.data
  } catch {
    ElMessage.error('加载竞品详情失败')
    router.push('/competitors')
  }
}

function toggleEdit() {
  if (editing.value) {
    editing.value = false
    return
  }
  if (!competitor.value) return
  const c = competitor.value
  Object.assign(editForm, {
    name: c.name,
    name_en: c.name_en || '',
    website: c.website || '',
    tier: c.tier,
    description: c.description || '',
    headquarters: c.headquarters || '',
    founded_year: c.founded_year || undefined,
    employee_count: c.employee_count || '',
    funding_stage: c.funding_stage || '',
    total_funding: c.total_funding || '',
    tags: c.tags ? [...c.tags] : [],
    is_active: c.is_active,
  })
  editing.value = true
}

async function saveBasicInfo() {
  if (!competitor.value) return
  saving.value = true
  try {
    const res = await competitorApi.update(competitor.value.id, editForm)
    competitor.value = res.data
    editing.value = false
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// ---------- 产品 ----------
const products = ref<Product[]>([])
const loadingProducts = ref(false)
const productDialogVisible = ref(false)
const productEditId = ref('')
const productSaving = ref(false)
const productFormRef = ref<FormInstance>()

const defaultProduct = {
  name: '',
  category: '',
  description: '',
  launch_date: '',
  pricing_model: '',
  target_market: '',
  website: '',
  tags: [] as string[],
  is_active: true,
}
const productForm = reactive({ ...defaultProduct })
const productRules: FormRules = {
  name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
}

async function fetchProducts() {
  if (!competitor.value) return
  loadingProducts.value = true
  try {
    const res = await competitorApi.listProducts(competitor.value.id)
    products.value = res.data.items
  } catch {
    ElMessage.error('加载产品列表失败')
  } finally {
    loadingProducts.value = false
  }
}

function openProductDialog(row?: Product) {
  if (row) {
    productEditId.value = row.id
    Object.assign(productForm, {
      name: row.name,
      category: row.category || '',
      description: row.description || '',
      launch_date: row.launch_date || '',
      pricing_model: row.pricing_model || '',
      target_market: row.target_market || '',
      website: row.website || '',
      tags: row.tags ? [...row.tags] : [],
      is_active: row.is_active,
    })
  } else {
    productEditId.value = ''
    Object.assign(productForm, { ...defaultProduct, tags: [] })
  }
  productDialogVisible.value = true
}

async function saveProduct() {
  if (!competitor.value) return
  const valid = await productFormRef.value?.validate().catch(() => false)
  if (!valid) return
  productSaving.value = true
  // 清理空字符串字段，后端 Optional 字段需要 null 而非 ""
  const payload: any = { ...productForm }
  // 日期字段：Date 对象转 ISO 字符串，空值转 null
  if (payload.launch_date instanceof Date) {
    payload.launch_date = payload.launch_date.toISOString()
  }
  for (const key of ['category', 'description', 'launch_date', 'pricing_model', 'target_market', 'website']) {
    if (payload[key] === '' || payload[key] === undefined) payload[key] = null
  }
  try {
    if (productEditId.value) {
      await competitorApi.updateProduct(competitor.value.id, productEditId.value, payload)
    } else {
      await competitorApi.createProduct(competitor.value.id, payload)
    }
    ElMessage.success(productEditId.value ? '更新成功' : '创建成功')
    productDialogVisible.value = false
    fetchProducts()
  } catch (err: any) {
    const msg = err.response?.data?.detail || err.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    productSaving.value = false
  }
}

// ---------- 功能对比 ----------
const features = ref<Feature[]>([])
const featureDialogVisible = ref(false)
const featureEditId = ref('')
const featureSaving = ref(false)
const featureFormRef = ref<FormInstance>()

const defaultFeature = {
  category: '',
  feature_name: '',
  support_level: 'unknown' as string,
  description: '',
  source_url: '',
}
const featureForm = reactive({ ...defaultFeature })
const featureRules: FormRules = {
  category: [{ required: true, message: '请选择或输入分类', trigger: 'blur' }],
  feature_name: [{ required: true, message: '请输入功能名称', trigger: 'blur' }],
  support_level: [{ required: true, message: '请选择支持程度', trigger: 'change' }],
}

const featureMap = computed(() => {
  const map: Record<string, Feature[]> = {}
  for (const f of features.value) {
    const cat = f.category || '未分类'
    if (!map[cat]) map[cat] = []
    map[cat].push(f)
  }
  return map
})

const featureCategories = computed(() => Object.keys(featureMap.value).sort())

const supportLabelMap: Record<string, string> = { full: '完全支持', partial: '部分支持', none: '不支持', unknown: '未知' }
const supportTagMap: Record<string, string> = { full: 'success', partial: 'warning', none: 'danger', unknown: 'info' }
function supportLabel(s: string) { return supportLabelMap[s] || s }
function supportTag(s: string) { return supportTagMap[s] || 'info' }

async function fetchFeatures() {
  if (!competitor.value) return
  try {
    const res = await competitorApi.listFeatures(competitor.value.id)
    features.value = res.data.items || []
  } catch {
    ElMessage.error('加载功能对比失败')
  }
}

function openFeatureDialog(row?: Feature) {
  if (row) {
    featureEditId.value = row.id
    Object.assign(featureForm, {
      category: row.category,
      feature_name: row.feature_name,
      support_level: row.support_level,
      description: row.description || '',
      source_url: row.source_url || '',
    })
  } else {
    featureEditId.value = ''
    Object.assign(featureForm, { ...defaultFeature })
  }
  featureDialogVisible.value = true
}

async function saveFeature() {
  if (!competitor.value) return
  const valid = await featureFormRef.value?.validate().catch(() => false)
  if (!valid) return
  featureSaving.value = true
  const payload: any = { ...featureForm }
  for (const key of ['description', 'source_url']) {
    if (payload[key] === '') payload[key] = null
  }
  try {
    await competitorApi.upsertFeature(competitor.value.id, payload)
    ElMessage.success(featureEditId.value ? '更新成功' : '创建成功')
    featureDialogVisible.value = false
    fetchFeatures()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    featureSaving.value = false
  }
}

// ---------- 价格历史 ----------
const pricingList = ref<PricingEntry[]>([])
const loadingPricing = ref(false)
const pricingDialogVisible = ref(false)
const pricingSaving = ref(false)
const pricingFormRef = ref<FormInstance>()

const defaultPricing = {
  plan_name: '',
  old_price: undefined as number | undefined,
  new_price: 0,
  currency: 'CNY',
  billing_cycle: '',
  change_type: '',
  change_description: '',
  source_url: '',
  detected_at: '',
}
const pricingForm = reactive({ ...defaultPricing })
const pricingRules: FormRules = {
  plan_name: [{ required: true, message: '请输入套餐名称', trigger: 'blur' }],
  new_price: [{ required: true, message: '请输入新价格', trigger: 'blur' }],
  detected_at: [{ required: true, message: '请选择发现时间', trigger: 'change' }],
}

const pricingChangeTagMap: Record<string, string> = { '新发布': 'success', '涨价': 'danger', '降价': 'success', '套餐调整': 'warning', '其他': 'info' }
function pricingChangeTag(t: string) { return pricingChangeTagMap[t] || 'info' }

async function fetchPricing() {
  if (!competitor.value) return
  loadingPricing.value = true
  try {
    const res = await competitorApi.listPricingHistory(competitor.value.id)
    pricingList.value = res.data.items
  } catch {
    ElMessage.error('加载价格历史失败')
  } finally {
    loadingPricing.value = false
  }
}

function openPricingDialog() {
  Object.assign(pricingForm, { ...defaultPricing })
  pricingDialogVisible.value = true
}

async function savePricing() {
  if (!competitor.value) return
  const valid = await pricingFormRef.value?.validate().catch(() => false)
  if (!valid) return
  pricingSaving.value = true
  const payload: any = { ...pricingForm, detected_at: pricingForm.detected_at || new Date().toISOString() }
  for (const key of ['old_price', 'change_type', 'change_description', 'source_url', 'billing_cycle']) {
    if (payload[key] === '' || payload[key] === undefined) payload[key] = null
  }
  try {
    await competitorApi.recordPricing(competitor.value.id, payload)
    ElMessage.success('记录成功')
    pricingDialogVisible.value = false
    fetchPricing()
  } catch {
    ElMessage.error('记录失败')
  } finally {
    pricingSaving.value = false
  }
}

// ---------- AI 竞品分析 ----------
const aiCompetitorLoading = ref(false)
const aiResult = ref<AICompetitorResult | null>(null)
const aiResultDialogVisible = ref(false)

async function handleAICompetitorAnalysis() {
  if (!competitor.value) return
  aiCompetitorLoading.value = true
  aiResult.value = null
  try {
    const res = await aiApi.competitorAnalysis(competitor.value.id)
    aiResult.value = res.data
    aiResultDialogVisible.value = true
    ElMessage.success('竞品 AI 分析完成')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || 'AI 竞品分析失败')
  } finally {
    aiCompetitorLoading.value = false
  }
}

// ---------- 工具 ----------
function formatDate(d: string) {
  if (!d) return '--'
  return new Date(d).toLocaleString('zh-CN')
}

function formatPrice(price: number, currency: string) {
  const symbols: Record<string, string> = { CNY: '¥', USD: '$', EUR: '€', JPY: '¥' }
  const sym = symbols[currency] || currency || ''
  return `${sym}${price.toLocaleString()}`
}

// ---------- Tab 切换时按需加载 ----------
const activeTab = ref('basic')

watch(activeTab, (tab) => {
  if (tab === 'products' && products.value.length === 0) fetchProducts()
  else if (tab === 'features' && features.value.length === 0) fetchFeatures()
  else if (tab === 'pricing' && pricingList.value.length === 0) fetchPricing()
})

onMounted(() => {
  fetchDetail()
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

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 { margin: 0; }

.header-actions { display: flex; gap: 8px; }

.info-card { margin-bottom: 16px; }

.info-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.info-meta h3 { margin: 0 0 4px; font-size: 18px; }
.info-meta p { margin: 0; color: #909399; font-size: 13px; }

.info-tags {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.detail-tabs { margin-top: 4px; }

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tab-title { font-weight: 600; font-size: 15px; }

.feature-group { margin-bottom: 20px; }

.feature-category {
  margin: 0 0 8px;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
  color: #606266;
}

.link {
  color: #409eff;
  text-decoration: none;
}

.link:hover { text-decoration: underline; }

.text-muted { color: #c0c4cc; }

.tag-item { margin-right: 6px; margin-bottom: 4px; }

.empty-block { padding: 40px 0; }

.price-new { font-weight: 500; color: #e6a23c; }
</style>
