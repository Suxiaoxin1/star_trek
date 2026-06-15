import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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
  ],
})

export default router
