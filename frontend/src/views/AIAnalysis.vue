<template>
  <div class="page">
    <div class="page-header">
      <h2>AI 智能分析</h2>
      <div class="header-right">
        <el-tag v-if="aiStatus.available" type="success" size="large">
          AI 可用 | {{ aiStatus.model }}
        </el-tag>
        <el-tag v-else type="danger" size="large">
          AI 不可用 | {{ aiStatus.message }}
        </el-tag>
      </div>
    </div>

    <!-- 操作步骤指引 -->
    <el-alert type="info" :closable="false" show-icon class="guide-alert" v-if="!activeFeature">
      <template #title>
        <span class="guide-title">开始使用 AI 智能分析</span>
      </template>
      <div class="guide-steps">
        <div class="guide-step"><span class="step-num">1</span> 选择下方的分析功能</div>
        <div class="guide-step"><span class="step-num">2</span> 输入待分析的文本或选择情报</div>
        <div class="guide-step"><span class="step-num">3</span> 点击按钮开始分析，查看结果</div>
      </div>
    </el-alert>

    <!-- 功能卡片 -->
    <el-row :gutter="20" class="feature-row">
      <!-- 情感分析 -->
      <el-col :span="8">
        <el-card shadow="hover" class="feature-card" @click="activeFeature = 'sentiment'">
          <div class="feature-icon sentiment-icon">😊</div>
          <h3>情感分析</h3>
          <p>对市场情报文本进行情感倾向分析，识别正面/中性/负面信号</p>
        </el-card>
      </el-col>
      <!-- 摘要提取 -->
      <el-col :span="8">
        <el-card shadow="hover" class="feature-card" @click="activeFeature = 'summary'">
          <div class="feature-icon summary-icon">📝</div>
          <h3>摘要提取</h3>
          <p>自动提取情报关键要点、影响评估和行动建议</p>
        </el-card>
      </el-col>
      <!-- 报告生成 -->
      <el-col :span="8">
        <el-card shadow="hover" class="feature-card" @click="activeFeature = 'report'">
          <div class="feature-icon report-icon">📊</div>
          <h3>AI 报告生成</h3>
          <p>基于情报数据自动生成竞品分析报告（支持流式输出）</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 情感分析面板 -->
    <el-card v-if="activeFeature === 'sentiment'" class="analysis-panel">
      <template #header>
        <div class="panel-header">
          <span>情感分析</span>
          <el-button-group>
            <el-button size="small" @click="sentimentMode = 'text'" :type="sentimentMode === 'text' ? 'primary' : ''">
              自由文本
            </el-button>
            <el-button size="small" @click="sentimentMode = 'intelligence'" :type="sentimentMode === 'intelligence' ? 'primary' : ''">
              指定情报
            </el-button>
          </el-button-group>
        </div>
      </template>

      <!-- 自由文本模式 -->
      <div v-if="sentimentMode === 'text'">
        <el-input
          v-model="sentimentText"
          type="textarea"
          :rows="4"
          placeholder="输入待分析的文本内容..."
        />
        <div class="action-bar">
          <el-button
            type="primary"
            :loading="sentimentLoading"
            :disabled="!sentimentText.trim()"
            @click="handleSentimentAnalysis"
          >
            <el-icon><MagicStick /></el-icon> 开始分析
          </el-button>
        </div>
      </div>

      <!-- 指定情报模式 -->
      <div v-if="sentimentMode === 'intelligence'">
        <el-select
          v-model="selectedIntelId"
          placeholder="选择要分析的情报"
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
        <div class="action-bar">
          <el-button
            type="primary"
            :loading="sentimentLoading"
            :disabled="!selectedIntelId"
            @click="handleIntelSentiment"
          >
            <el-icon><MagicStick /></el-icon> 分析情报情感
          </el-button>
        </div>
      </div>

      <!-- 结果展示 -->
      <div v-if="sentimentResult" class="result-section">
        <el-descriptions title="情感分析结果" :column="2" border>
          <el-descriptions-item label="情感倾向">
            <el-tag :type="sentimentTagType(sentimentResult.sentiment)" size="large">
              {{ sentimentLabel(sentimentResult.sentiment) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="情感分数">
            <el-progress
              :percentage="Math.round(sentimentResult.sentiment_score * 100)"
              :color="sentimentColor(sentimentResult.sentiment)"
              :stroke-width="20"
            />
          </el-descriptions-item>
          <el-descriptions-item label="置信度">
            <el-progress :percentage="Math.round(sentimentResult.confidence * 100)" :stroke-width="16" />
          </el-descriptions-item>
          <el-descriptions-item label="分析理由">
            {{ sentimentResult.reasoning }}
          </el-descriptions-item>
          <el-descriptions-item v-if="sentimentResult.key_phrases?.length" label="关键短语" :span="2">
            <el-tag v-for="phrase in sentimentResult.key_phrases" :key="phrase" size="small" class="phrase-tag">
              {{ phrase }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 摘要提取面板 -->
    <el-card v-if="activeFeature === 'summary'" class="analysis-panel">
      <template #header>
        <div class="panel-header">
          <span>摘要提取</span>
          <el-button-group>
            <el-button size="small" @click="summaryMode = 'text'" :type="summaryMode === 'text' ? 'primary' : ''">
              自由文本
            </el-button>
            <el-button size="small" @click="summaryMode = 'intelligence'" :type="summaryMode === 'intelligence' ? 'primary' : ''">
              指定情报
            </el-button>
          </el-button-group>
        </div>
      </template>

      <div v-if="summaryMode === 'text'">
        <el-input
          v-model="summaryText"
          type="textarea"
          :rows="6"
          placeholder="输入待提取摘要的情报文本..."
        />
        <div class="action-bar">
          <el-button
            type="primary"
            :loading="summaryLoading"
            :disabled="!summaryText.trim()"
            @click="handleSummaryExtraction"
          >
            <el-icon><MagicStick /></el-icon> 提取摘要
          </el-button>
        </div>
      </div>

      <div v-if="summaryMode === 'intelligence'">
        <el-select
          v-model="selectedIntelId"
          placeholder="选择要提取摘要的情报"
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
        <div class="action-bar">
          <el-button
            type="primary"
            :loading="summaryLoading"
            :disabled="!selectedIntelId"
            @click="handleIntelSummary"
          >
            <el-icon><MagicStick /></el-icon> 提取情报摘要
          </el-button>
        </div>
      </div>

      <!-- 摘要结果 -->
      <div v-if="summaryResult" class="result-section">
        <el-descriptions title="摘要提取结果" :column="1" border>
          <el-descriptions-item label="核心摘要">
            <div class="summary-content">{{ summaryResult.summary }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="影响级别">
            <el-tag :type="impactTagType(summaryResult.impact_level)">
              {{ impactLabel(summaryResult.impact_level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="summaryResult.key_points?.length" label="关键要点">
            <ul class="key-points-list">
              <li v-for="point in summaryResult.key_points" :key="point">{{ point }}</li>
            </ul>
          </el-descriptions-item>
          <el-descriptions-item v-if="summaryResult.affected_areas?.length" label="受影响领域">
            <el-tag v-for="area in summaryResult.affected_areas" :key="area" size="small" class="phrase-tag">
              {{ area }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="summaryResult.action_items?.length" label="建议行动">
            <ul class="action-list">
              <li v-for="item in summaryResult.action_items" :key="item">{{ item }}</li>
            </ul>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 报告生成面板 -->
    <el-card v-if="activeFeature === 'report'" class="analysis-panel">
      <template #header>
        <div class="panel-header">
          <span>AI 报告生成</span>
          <el-tag v-if="streamGenerating" type="warning" size="small">正在流式生成...</el-tag>
        </div>
      </template>

      <el-form :model="reportForm" label-width="100px">
        <el-form-item label="报告标题">
          <el-input v-model="reportForm.title" placeholder="留空则自动生成标题" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="关联竞品">
              <el-select
                v-model="reportForm.competitor_id"
                placeholder="选择竞品（获取关联情报）"
                filterable
                clearable
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
          </el-col>
          <el-col :span="12">
            <el-form-item label="报告类型">
              <el-select v-model="reportForm.report_type" style="width: 100%">
                <el-option label="竞品分析" value="competitor_analysis" />
                <el-option label="SWOT分析" value="swot" />
                <el-option label="趋势报告" value="trend" />
                <el-option label="预警报告" value="alert" />
                <el-option label="季度报告" value="quarterly" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="指定情报">
          <el-select
            v-model="reportForm.intelligence_ids"
            multiple
            filterable
            placeholder="选择特定情报（可选，否则自动获取竞品关联情报）"
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
        <el-form-item label="生成方式">
          <el-radio-group v-model="reportMode">
            <el-radio value="sync">同步生成（完整结果）</el-radio>
            <el-radio value="stream">流式生成（实时展示）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="reportForm.tags"
            multiple
            filterable
            allow-create
            placeholder="输入标签后回车"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <div class="action-bar">
        <el-button
          type="primary"
          :loading="reportLoading || streamGenerating"
          :disabled="!aiStatus.available"
          @click="handleGenerateReport"
        >
          <el-icon><MagicStick /></el-icon>
          {{ reportMode === 'stream' ? '流式生成报告' : '生成报告' }}
        </el-button>
      </div>

      <!-- 同步生成结果 -->
      <div v-if="reportResult && reportMode === 'sync'" class="result-section">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="报告标题">{{ reportResult.title }}</el-descriptions-item>
          <el-descriptions-item label="生成方式">
            <el-tag type="success" size="small">AI 生成</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <div class="report-preview">
          <h4>报告内容预览</h4>
          <div class="markdown-body" v-html="renderMarkdown(reportResult.content || '')"></div>
        </div>
      </div>

      <!-- 流式生成结果 -->
      <div v-if="streamContent" class="result-section">
        <div class="stream-preview">
          <div class="stream-header">
            <h4>实时生成中...</h4>
            <el-button v-if="streamDone" type="success" size="small" @click="goToReport(streamReportId)">
              查看完整报告
            </el-button>
          </div>
          <div class="markdown-body" v-html="renderMarkdown(streamContent)"></div>
        </div>
      </div>
    </el-card>

    <!-- 竞品深度分析面板 -->
    <el-card v-if="activeFeature === 'competitor'" class="analysis-panel">
      <template #header>
        <div class="panel-header">
          <span>竞品深度分析</span>
        </div>
      </template>

      <el-form :model="competitorForm" label-width="100px">
        <el-form-item label="选择竞品">
          <el-select
            v-model="competitorForm.competitor_id"
            placeholder="选择要深度分析的竞品"
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
      </el-form>

      <div class="action-bar">
        <el-button
          type="primary"
          :loading="competitorLoading"
          :disabled="!competitorForm.competitor_id || !aiStatus.available"
          @click="handleCompetitorAnalysis"
        >
          <el-icon><MagicStick /></el-icon> 开始深度分析
        </el-button>
      </div>

      <!-- 分析结果 -->
      <div v-if="competitorResult" class="result-section">
        <h3>{{ competitorResult.competitor_name }} 竞品深度分析</h3>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card shadow="never" class="swot-card strength">
              <h4>核心优势</h4>
              <ul>
                <li v-for="s in competitorResult.strengths" :key="s">{{ s }}</li>
              </ul>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" class="swot-card weakness">
              <h4>主要劣势</h4>
              <ul>
                <li v-for="w in competitorResult.weaknesses" :key="w">{{ w }}</li>
              </ul>
            </el-card>
          </el-col>
        </el-row>
        <el-descriptions :column="2" border style="margin-top: 16px">
          <el-descriptions-item label="市场定位">{{ competitorResult.market_position }}</el-descriptions-item>
          <el-descriptions-item label="威胁等级">
            <el-tag :type="threatTagType(competitorResult.threat_level)">
              {{ threatLabel(competitorResult.threat_level) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="8">
            <el-card shadow="never" class="insight-card">
              <h4>我方机会</h4>
              <ul>
                <li v-for="o in competitorResult.opportunity_for_us" :key="o">{{ o }}</li>
              </ul>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never" class="insight-card">
              <h4>策略建议</h4>
              <ul>
                <li v-for="r in competitorResult.strategic_recommendations" :key="r">{{ r }}</li>
              </ul>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="never" class="insight-card">
              <h4>风险因素</h4>
              <ul>
                <li v-for="r in competitorResult.risk_factors" :key="r">{{ r }}</li>
              </ul>
            </el-card>
          </el-col>
        </el-row>
        <el-card v-if="competitorResult.recent_highlights?.length" shadow="never" class="insight-card" style="margin-top: 16px">
          <h4>近期重要动向</h4>
          <ul>
            <li v-for="h in competitorResult.recent_highlights" :key="h">{{ h }}</li>
          </ul>
        </el-card>
      </div>
    </el-card>

    <!-- 功能切换按钮 -->
    <el-row :gutter="12" class="feature-switch-row" v-if="activeFeature">
      <el-col :span="6">
        <el-button :type="activeFeature === 'sentiment' ? 'primary' : 'default'" @click="activeFeature = 'sentiment'" long>
          情感分析
        </el-button>
      </el-col>
      <el-col :span="6">
        <el-button :type="activeFeature === 'summary' ? 'primary' : 'default'" @click="activeFeature = 'summary'" long>
          摘要提取
        </el-button>
      </el-col>
      <el-col :span="6">
        <el-button :type="activeFeature === 'report' ? 'primary' : 'default'" @click="activeFeature = 'report'" long>
          报告生成
        </el-button>
      </el-col>
      <el-col :span="6">
        <el-button :type="activeFeature === 'competitor' ? 'primary' : 'default'" @click="activeFeature = 'competitor'" long>
          竞品分析
        </el-button>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { aiApi } from '@/api/ai'
import { intelligenceApi } from '@/api/intelligence'
import { competitorApi } from '@/api/competitors'
import type {
  AIStatus,
  AISentimentResult,
  AISummaryResult,
  AICompetitorResult,
  Report,
  Intelligence,
  Competitor,
} from '@/types'

const router = useRouter()

// ────────────── AI 状态 ──────────────
const aiStatus = reactive<AIStatus>({
  available: false,
  model: null,
  api_base: '',
  message: '正在检测...',
})

async function checkAIStatus() {
  try {
    const res = await aiApi.status()
    Object.assign(aiStatus, res.data)
  } catch {
    aiStatus.available = false
    aiStatus.message = '检测失败，请检查后端服务'
  }
}

// ────────────── 功能切换 ──────────────
const activeFeature = ref<string>('sentiment')

// ────────────── 数据选项 ──────────────
const competitorOptions = ref<{ id: string; name: string }[]>([])
const intelOptions = ref<{ id: string; title: string }[]>([])
const selectedIntelId = ref('')

async function fetchOptions() {
  try {
    const compRes = await competitorApi.list({ page_size: 999 })
    competitorOptions.value = compRes.data.items.map((c: Competitor) => ({
      id: c.id,
      name: c.name,
    }))
    const intelRes = await intelligenceApi.list({ page_size: 100 })
    intelOptions.value = intelRes.data.items.map((i: Intelligence) => ({
      id: i.id,
      title: i.title,
    }))
  } catch {
    // ignore
  }
}

// ────────────── 情感分析 ──────────────
const sentimentMode = ref<'text' | 'intelligence'>('text')
const sentimentText = ref('')
const sentimentLoading = ref(false)
const sentimentResult = ref<AISentimentResult | null>(null)

function sentimentLabel(s: string) {
  const map: Record<string, string> = { positive: '正面', neutral: '中性', negative: '负面' }
  return map[s] || s
}

function sentimentTagType(s: string) {
  const map: Record<string, string> = { positive: 'success', neutral: 'info', negative: 'danger' }
  return map[s] || ''
}

function sentimentColor(s: string) {
  const map: Record<string, string> = { positive: '#67c23a', neutral: '#409eff', negative: '#f56c6c' }
  return map[s] || '#409eff'
}

async function handleSentimentAnalysis() {
  if (!sentimentText.value.trim()) return
  sentimentLoading.value = true
  sentimentResult.value = null
  try {
    const res = await aiApi.sentiment(sentimentText.value)
    sentimentResult.value = res.data
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '情感分析失败')
  } finally {
    sentimentLoading.value = false
  }
}

async function handleIntelSentiment() {
  if (!selectedIntelId.value) return
  sentimentLoading.value = true
  sentimentResult.value = null
  try {
    const res = await aiApi.intelligenceSentiment(selectedIntelId.value)
    sentimentResult.value = res.data
    ElMessage.success('情报情感已更新')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '情报情感分析失败')
  } finally {
    sentimentLoading.value = false
  }
}

// ────────────── 摘要提取 ──────────────
const summaryMode = ref<'text' | 'intelligence'>('text')
const summaryText = ref('')
const summaryLoading = ref(false)
const summaryResult = ref<AISummaryResult | null>(null)

function impactLabel(level: string) {
  const map: Record<string, string> = { high: '高', medium: '中', low: '低' }
  return map[level] || level
}

function impactTagType(level: string) {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'info' }
  return map[level] || ''
}

async function handleSummaryExtraction() {
  if (!summaryText.value.trim()) return
  summaryLoading.value = true
  summaryResult.value = null
  try {
    const res = await aiApi.summary(summaryText.value)
    summaryResult.value = res.data
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '摘要提取失败')
  } finally {
    summaryLoading.value = false
  }
}

async function handleIntelSummary() {
  if (!selectedIntelId.value) return
  summaryLoading.value = true
  summaryResult.value = null
  try {
    const res = await aiApi.intelligenceSummary(selectedIntelId.value)
    summaryResult.value = res.data
    ElMessage.success('情报摘要已更新')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '情报摘要提取失败')
  } finally {
    summaryLoading.value = false
  }
}

// ────────────── 报告生成 ──────────────
const reportMode = ref<'sync' | 'stream'>('stream')
const reportLoading = ref(false)
const streamGenerating = ref(false)
const streamContent = ref('')
const streamDone = ref(false)
const streamReportId = ref('')
const reportResult = ref<Report | null>(null)

const reportForm = reactive({
  title: '',
  competitor_id: '',
  intelligence_ids: [] as string[],
  report_type: 'competitor_analysis',
  tags: ['AI生成'] as string[],
})

async function handleGenerateReport() {
  if (reportMode.value === 'stream') {
    await handleStreamReport()
  } else {
    await handleSyncReport()
  }
}

async function handleSyncReport() {
  reportLoading.value = true
  reportResult.value = null
  try {
    const res = await aiApi.generateReport({
      title: reportForm.title || undefined,
      competitor_id: reportForm.competitor_id || undefined,
      intelligence_ids: reportForm.intelligence_ids.length > 0 ? reportForm.intelligence_ids : undefined,
      report_type: reportForm.report_type,
      tags: reportForm.tags,
    })
    reportResult.value = res.data
    ElMessage.success('报告已生成并保存')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '报告生成失败')
  } finally {
    reportLoading.value = false
  }
}

async function handleStreamReport() {
  streamGenerating.value = true
  streamContent.value = ''
  streamDone.value = false
  streamReportId.value = ''

  try {
    const response = await aiApi.streamReport({
      title: reportForm.title || undefined,
      competitor_id: reportForm.competitor_id || undefined,
      intelligence_ids: reportForm.intelligence_ids.length > 0 ? reportForm.intelligence_ids : undefined,
      report_type: reportForm.report_type,
      tags: reportForm.tags,
    })

    if (!response.ok) {
      const err = await response.json()
      ElMessage.error(err.detail || '流式生成失败')
      return
    }

    const reader = response.body?.getReader()
    if (!reader) {
      ElMessage.error('无法读取流式响应')
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.error) {
              ElMessage.error(data.error)
              streamGenerating.value = false
              return
            }
            if (data.chunk) {
              streamContent.value += data.chunk
            }
            if (data.done) {
              streamDone.value = true
              streamReportId.value = data.report_id
              ElMessage.success('报告生成完成并保存')
            }
          } catch {
            // ignore malformed data
          }
        }
      }
    }
  } catch (e: any) {
    ElMessage.error('流式生成失败: ' + e.message)
  } finally {
    streamGenerating.value = false
  }
}

function goToReport(id: string) {
  if (id) {
    router.push('/reports')
  }
}

// ────────────── 竞品深度分析 ──────────────
const competitorForm = reactive({ competitor_id: '' })
const competitorLoading = ref(false)
const competitorResult = ref<AICompetitorResult | null>(null)

function threatLabel(level: string) {
  const map: Record<string, string> = { high: '高威胁', medium: '中威胁', low: '低威胁' }
  return map[level] || level
}

function threatTagType(level: string) {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'info' }
  return map[level] || ''
}

async function handleCompetitorAnalysis() {
  if (!competitorForm.competitor_id) return
  competitorLoading.value = true
  competitorResult.value = null
  try {
    const res = await aiApi.competitorAnalysis(competitorForm.competitor_id)
    competitorResult.value = res.data
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '竞品分析失败')
  } finally {
    competitorLoading.value = false
  }
}

// ────────────── Markdown 渲染 ──────────────
function renderMarkdown(content: string) {
  if (!content) return '<p class="text-muted">暂无内容</p>'
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`(.+?)`/g, '<code>$1</code>')
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>')
  // 表格
  html = html.replace(/\|(.+)\|/g, (match) => {
    const cells = match.split('|').filter(c => c.trim())
    return '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>'
  })
  html = html.replace(/(<tr>.*<\/tr>)/gs, '<table border="1">$1</table>')
  // 列表
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
  html = html.replace(/\n\n/g, '</p><p>')
  html = html.replace(/\n/g, '<br>')
  html = '<p>' + html + '</p>'
  html = html.replace(/<p>\s*<\/p>/g, '')
  return html
}

// ────────────── 初始化 ──────────────
onMounted(() => {
  checkAIStatus()
  fetchOptions()
})
</script>

<style scoped>
.page { padding: 0 10px; }

/* 操作指引 */
.guide-alert { margin-bottom: 20px; }

.guide-title {
  font-weight: 600;
  font-size: 14px;
}

.guide-steps {
  display: flex;
  gap: 32px;
  margin-top: 8px;
}

.guide-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 { margin: 0; }

/* 功能卡片 */
.feature-row { margin-bottom: 20px; }

.feature-card {
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
  min-height: 160px;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.feature-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.sentiment-icon { color: #e6a23c; }
.summary-icon { color: #409eff; }
.report-icon { color: #67c23a; }

.feature-card h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #303133;
}

.feature-card p {
  margin: 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

/* 分析面板 */
.analysis-panel { margin-bottom: 20px; }

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 结果展示 */
.result-section {
  margin-top: 20px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.result-section h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #303133;
}

.phrase-tag { margin-right: 6px; margin-bottom: 4px; }

.summary-content {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  white-space: pre-wrap;
}

.key-points-list,
.action-list {
  padding-left: 18px;
  margin: 0;
}

.key-points-list li,
.action-list li {
  margin-bottom: 6px;
  font-size: 14px;
  color: #303133;
  line-height: 1.5;
}

/* 报告预览 */
.report-preview,
.stream-preview {
  margin-top: 16px;
}

.report-preview h4,
.stream-preview h4 {
  margin: 0 0 12px;
  font-size: 15px;
}

.stream-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stream-header h4 { margin: 0; }

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
.markdown-body :deep(code) { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }
.markdown-body :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; }
.markdown-body :deep(td) { padding: 8px 12px; border: 1px solid #ddd; }

/* SWOT 卡片 */
.swot-card { margin-bottom: 0; }

.swot-card h4 {
  margin: 0 0 12px;
  font-size: 14px;
}

.swot-card ul {
  padding-left: 16px;
  margin: 0;
}

.swot-card li {
  margin-bottom: 6px;
  font-size: 13px;
}

.strength { border-left: 3px solid #67c23a; }
.weakness { border-left: 3px solid #f56c6c; }

.insight-card h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #606266;
}

.insight-card ul {
  padding-left: 16px;
  margin: 0;
}

.insight-card li {
  margin-bottom: 6px;
  font-size: 13px;
}

/* 功能切换 */
.feature-switch-row { margin-top: 16px; }

.text-muted { color: #c0c4cc; }
</style>