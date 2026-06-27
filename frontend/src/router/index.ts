import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录', public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '仪表盘' },
    },
    {
      path: '/competitors',
      name: 'competitors',
      component: () => import('@/views/Competitors.vue'),
      meta: { title: '竞品管理' },
    },
    {
      path: '/competitors/:id',
      name: 'competitor-detail',
      component: () => import('@/views/CompetitorDetail.vue'),
      meta: { title: '竞品详情' },
    },
    {
      path: '/intelligence',
      name: 'intelligence',
      component: () => import('@/views/Intelligence.vue'),
      meta: { title: '市场情报' },
    },
    {
      path: '/reports',
      name: 'reports',
      component: () => import('@/views/Reports.vue'),
      meta: { title: '分析报告' },
    },
    {
      path: '/alerts',
      name: 'alerts',
      component: () => import('@/views/Alerts.vue'),
      meta: { title: '预警中心' },
    },
    {
      path: '/datasources',
      name: 'datasources',
      component: () => import('@/views/DataSources.vue'),
      meta: { title: '数据源管理' },
    },
    {
      path: '/collected-data',
      name: 'collected-data',
      component: () => import('@/views/CollectedData.vue'),
      meta: { title: '采集数据' },
    },
    {
      path: '/ai-analysis',
      name: 'ai-analysis',
      component: () => import('@/views/AIAnalysis.vue'),
      meta: { title: 'AI 智能分析' },
    },
  ],
})

// 路由守卫：未登录跳转登录页
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // 初始化用户信息（刷新页面时从 token 恢复）
  if (authStore.accessToken && !authStore.user) {
    await authStore.init()
  }

  // 公开页面直接放行
  if (to.meta.public) {
    // 已登录用户访问登录页，重定向到首页
    if (authStore.isLoggedIn && to.name === 'login') {
      next({ name: 'dashboard' })
      return
    }
    next()
    return
  }

  // 需要认证的页面
  if (!authStore.isLoggedIn) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
