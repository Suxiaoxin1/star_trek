<template>
  <!-- 未登录：只渲染路由出口（登录页占满全屏） -->
  <router-view v-if="!authStore.isLoggedIn" />

  <!-- 已登录：完整布局（侧边栏 + 顶栏 + 主内容区） -->
  <el-container v-else class="layout">
    <el-aside width="230px">
      <!-- Logo 区域 -->
      <div class="logo-area">
        <div class="logo-icon">
          <svg viewBox="0 0 32 32" width="28" height="28" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="8" fill="url(#logo-grad)"/>
            <path d="M8 16L14 10L20 16L14 22Z" fill="white" opacity="0.9"/>
            <path d="M14 10L20 16L26 10" stroke="white" stroke-width="1.5" opacity="0.6"/>
            <defs><linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32"><stop stop-color="#667eea"/><stop offset="1" stop-color="#764ba2"/></linearGradient></defs>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-title">竞品分析系统</span>
          <span class="logo-sub">CI Platform</span>
        </div>
      </div>

      <!-- 侧边导航 -->
      <el-menu :router="true" :default-active="route.path" class="menu">
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/competitors">
          <el-icon><OfficeBuilding /></el-icon>
          <span>竞品管理</span>
        </el-menu-item>
        <el-menu-item index="/intelligence">
          <el-icon><TrendCharts /></el-icon>
          <span>市场情报</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <span>分析报告</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <span>预警中心</span>
        </el-menu-item>

        <el-divider class="menu-divider" />

        <el-menu-item index="/datasources">
          <el-icon><Link /></el-icon>
          <span>数据源管理</span>
        </el-menu-item>
        <el-menu-item index="/collected-data">
          <el-icon><Download /></el-icon>
          <span>采集数据</span>
        </el-menu-item>

        <el-divider class="menu-divider" />

        <el-menu-item index="/ai-analysis">
          <el-icon><MagicStick /></el-icon>
          <span>AI 智能分析</span>
        </el-menu-item>
      </el-menu>

      <!-- 侧边栏底部版本信息 -->
      <div class="sidebar-footer">
        <span class="version-tag">v0.1.0</span>
      </div>
    </el-aside>

    <el-container>
      <el-header class="top-header">
        <div class="header-left">
          <span class="header-title">{{ route.meta?.title || '' }}</span>
          <!-- 操作指引提示图标 -->
          <el-tooltip v-if="pageTip" :content="pageTip" placement="bottom-start" :show-after="500">
            <el-icon class="tip-icon" @click="showTipDialog = true"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
        <div class="header-right">
          <!-- 新手指引按钮：显眼可见，方便新用户 -->
          <el-button type="primary" plain size="small" class="tour-btn" @click="showTipDialog = true">
            <el-icon :size="14"><InfoFilled /></el-icon>
            <span>新手指引</span>
          </el-button>
          <!-- 未读预警快捷入口 -->
          <el-badge v-if="unreadAlerts > 0" :value="unreadAlerts" :max="99" class="alert-badge">
            <el-button text @click="router.push('/alerts')">
              <el-icon :size="18"><Bell /></el-icon>
            </el-button>
          </el-badge>
          <el-dropdown trigger="click" @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" :style="{ background: avatarColor }" />
              <span class="user-name">{{ authStore.displayName }}</span>
              <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <el-icon><User /></el-icon>
                  {{ authStore.user?.email }}
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- 页面操作指引对话框 -->
    <el-dialog v-model="showTipDialog" :title="(route.meta?.title || '系统') + ' — 操作指引'" width="520px" :close-on-click-modal="true">
      <!-- 系统使用流程（横向 1 行 + 简短标签） -->
      <div v-if="route.path !== '/'" class="system-tour">
        <div class="tour-title">🗺️ 使用流程</div>
        <div class="tour-steps-compact">
          <div class="tour-step-compact">
            <div class="tour-step-num">1</div>
            <div class="tour-step-name">竞品</div>
          </div>
          <div class="tour-arrow">
            <el-icon :size="20"><Right /></el-icon>
          </div>
          <div class="tour-step-compact">
            <div class="tour-step-num">2</div>
            <div class="tour-step-name">数据源</div>
          </div>
          <div class="tour-arrow">
            <el-icon :size="20"><Right /></el-icon>
          </div>
          <div class="tour-step-compact">
            <div class="tour-step-num">3</div>
            <div class="tour-step-name">情报</div>
          </div>
          <div class="tour-arrow">
            <el-icon :size="20"><Right /></el-icon>
          </div>
          <div class="tour-step-compact">
            <div class="tour-step-num">4</div>
            <div class="tour-step-name">AI 分析</div>
          </div>
        </div>
        <el-divider class="compact-divider" />
      </div>

      <!-- 本页操作指引（精简版：3 个最关键动作） -->
      <div v-if="pageTipActions.length > 0" class="tip-dialog-content">
        <ul class="action-list">
          <li v-for="(action, idx) in pageTipActions" :key="idx">
            <el-icon class="action-icon"><CaretRight /></el-icon>
            <span>{{ action }}</span>
          </li>
        </ul>
      </div>
      <div v-else class="tip-dialog-content">
        <p>系统总览页面，点击左侧菜单切换不同模块。</p>
      </div>

      <template #footer>
        <div class="tip-dialog-footer">
          <el-checkbox v-model="hideOnNextVisit">不再自动显示</el-checkbox>
          <el-button type="primary" @click="dismissTip">知道了</el-button>
        </div>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { alertApi } from '@/api/alerts'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 未读预警数量
const unreadAlerts = ref(0)
const showTipDialog = ref(false)
const hideOnNextVisit = ref(false)

// 新用户引导：第一次访问时自动弹窗
const TIP_DISMISSED_KEY = 'ci_tip_dismissed'

function checkFirstTimeTip() {
  // 未登录或登录页不弹
  if (!authStore.isLoggedIn || route.path === '/login') return
  // 用户没关过引导（localStorage 没记录）就显示
  if (!localStorage.getItem(TIP_DISMISSED_KEY)) {
    // 延迟一点弹窗，让页面先渲染
    setTimeout(() => {
      showTipDialog.value = true
    }, 800)
  }
}

function dismissTip() {
  if (hideOnNextVisit.value) {
    localStorage.setItem(TIP_DISMISSED_KEY, '1')
  }
  showTipDialog.value = false
}

async function fetchUnreadAlerts() {
  try {
    const res = await alertApi.stats()
    unreadAlerts.value = res.data.unread_alerts || 0
  } catch { /* ignore */ }
}

// 路由切换时，如果用户没看过引导，切换到新页面也展示当前页的指引
watch(
  () => route.path,
  () => {
    checkFirstTimeTip()
  }
)

// 定时刷新（每 60 秒）
onMounted(() => {
  fetchUnreadAlerts()
  setInterval(fetchUnreadAlerts, 60000)
  checkFirstTimeTip()
})

const roleLabel = computed(() => {
  const map: Record<string, string> = { admin: '管理员', analyst: '分析师', viewer: '观察者' }
  return map[authStore.userRole] || authStore.userRole
})

const roleTagType = computed(() => {
  const map: Record<string, string> = { admin: 'danger', analyst: 'warning', viewer: 'info' }
  return map[authStore.userRole] || 'info'
})

// 头像颜色根据角色区分
const avatarColor = computed(() => {
  const map: Record<string, string> = { admin: '#f56c6c', analyst: '#e6a23c', viewer: '#909399' }
  return map[authStore.userRole] || '#409eff'
})

// 各页面操作指引（精简：每页 3 个最关键动作）
const pageTips: Record<string, { tip: string; actions: string[] }> = {
  '/': {
    tip: '系统核心数据概览',
    actions: [
      '点击统计卡片快速跳转到对应模块',
      '「情报分类分布」查看各分类情报数量',
      '「最新动态」时间线展示最近 8 条情报',
    ],
  },
  '/competitors': {
    tip: '建立竞争对手档案',
    actions: [
      '点击「新增竞品」添加对手',
      '点击「详情」管理产品/特性/价格',
      '使用筛选栏按层级/状态快速查找',
    ],
  },
  '/intelligence': {
    tip: '查看和管理市场情报',
    actions: [
      '点击「新增情报」手动添加动态',
      '使用筛选栏按竞品/分类/情感筛选',
      '点击「AI 情感分析」批量分析',
    ],
  },
  '/reports': {
    tip: '管理 AI 生成的分析报告',
    actions: [
      '报告可由 AI 自动生成或手动创建',
      '状态：草稿 → 进行中 → 已完成 → 已归档',
      '点击标题查看 Markdown 渲染内容',
    ],
  },
  '/alerts': {
    tip: '配置预警规则，命中关键词自动告警',
    actions: [
      '「预警规则」：定义关键词和严重程度',
      '「预警历史」：查看已触发的预警',
      '点击「标记已读/已处理」跟踪处置状态',
    ],
  },
  '/datasources': {
    tip: '配置数据采集来源（RSS/API/爬虫）',
    actions: [
      '点击「新增数据源」添加采集源',
      '设置采集间隔，系统自动定时抓取',
      '点击「触发采集」手动执行一次',
    ],
  },
  '/collected-data': {
    tip: '查看自动采集到的原始内容',
    actions: [
      '系统按数据源配置的频率自动采集',
      '点击「标记处理」标记为已处理',
      '在「市场情报」将采集内容转为正式情报',
    ],
  },
  '/ai-analysis': {
    tip: 'AI 智能分析（需配置 OPENAI_API_KEY）',
    actions: [
      '情感分析：判断文本正负面',
      '摘要提取：压缩长文为关键要点',
      '报告生成 / 竞品深度分析：选情报后生成',
    ],
  },
}

const pageTip = computed(() => pageTips[route.path]?.tip || '')
const pageTipActions = computed(() => pageTips[route.path]?.actions || [])

function handleUserCommand(command: string) {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style>
/* 全局重置 */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f0f2f5;
}

.layout {
  height: 100vh;
}

/* ===== 侧边栏 ===== */
.el-aside {
  background: #001529;
  color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.logo-area {
  height: 72px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.logo-icon {
  flex-shrink: 0;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 16px;
  font-weight: 700;
  color: white;
  line-height: 1.3;
  letter-spacing: 0.5px;
}

.logo-sub {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 1px;
}

.menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.menu-divider {
  margin: 4px 20px;
  border-color: rgba(255, 255, 255, 0.06);
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.version-tag {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
}

/* ===== 顶栏 ===== */
.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.tip-icon {
  font-size: 16px;
  color: #909399;
  cursor: pointer;
  transition: color 0.2s;
}

.tip-icon:hover {
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tour-btn {
  font-weight: 500;
  border-radius: 16px;
  padding: 5px 12px;
}

.alert-badge {
  line-height: 1;
}

.alert-badge .el-button {
  padding: 4px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f5f7fa;
}

.user-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

/* ===== 主内容区 ===== */
.main-content {
  background: #f0f2f5;
  min-height: 0;
}

/* ===== 指引对话框 ===== */
.tip-dialog-content {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
}

.tip-dialog-content b {
  color: #409eff;
}

.tip-dialog-content ol,
.tip-dialog-content ul {
  padding-left: 20px;
  margin: 8px 0;
}

.tip-dialog-content li {
  margin-bottom: 6px;
}

.tip-dialog-content p {
  margin: 8px 0;
}

/* ===== 新手指引弹窗：精简版 ===== */
.system-tour {
  margin-bottom: 4px;
}

.tour-title {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 10px;
}

/* 横向 1 行的紧凑步骤 */
.tour-steps-compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.tour-step-compact {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
}

.tour-step-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tour-step-name {
  font-size: 12px;
  font-weight: 500;
  color: #303133;
}

.tour-arrow {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
  background: linear-gradient(90deg, #c0d8ff 0%, #409eff 50%, #c0d8ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 18px;
  font-weight: 700;
  position: relative;
  padding: 0 4px;
  min-width: 24px;
}

.tour-arrow .el-icon {
  color: #409eff;
  background: #e8f0fe;
  border-radius: 50%;
  padding: 4px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.compact-divider {
  margin: 12px 0 8px;
}

/* 精简动作列表 */
.tip-dialog-content {
  font-size: 13px;
  line-height: 1.7;
  color: #303133;
}

.action-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.action-list li {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}

.action-icon {
  color: #409eff;
  font-size: 14px;
  flex-shrink: 0;
}

.tip-dialog-content p {
  margin: 4px 0;
  color: #606266;
}

.hide-tip-checkbox {
  margin-right: 16px;
}

/* 弹窗底部 footer：用 flex 容器，强制对齐与间距 */
.tip-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 32px;
  padding: 0 8px;
}

.tip-dialog-footer .el-checkbox {
  margin-right: 0;
}
</style>
