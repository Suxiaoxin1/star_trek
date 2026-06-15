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
      </el-menu>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
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
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.menu {
  border-right: none;
}
</style>
