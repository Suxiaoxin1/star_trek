<template>
  <el-container class="layout">
    <el-aside width="220px">
      <div class="logo">竞品分析系统</div>
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
        <el-menu-item index="/datasources">
          <el-icon><Link /></el-icon>
          <span>数据源管理</span>
        </el-menu-item>
        <el-menu-item index="/collected-data">
          <el-icon><Download /></el-icon>
          <span>采集数据</span>
        </el-menu-item>
        <el-menu-item index="/ai-analysis">
          <el-icon><MagicStick /></el-icon>
          <span>AI 智能分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="top-header">
        <span class="header-title">{{ route.meta?.title || '' }}</span>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
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

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const roleLabel = computed(() => {
  const map: Record<string, string> = { admin: '管理员', analyst: '分析师', viewer: '观察者' }
  return map[authStore.userRole] || authStore.userRole
})

const roleTagType = computed(() => {
  const map: Record<string, string> = { admin: 'danger', analyst: 'warning', viewer: 'info' }
  return map[authStore.userRole] || 'info'
})

function handleUserCommand(command: string) {
  if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.layout {
  height: 100vh;
}

.el-aside {
  background: #001529;
  color: white;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.menu {
  border-right: none;
}

.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 24px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
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
</style>
