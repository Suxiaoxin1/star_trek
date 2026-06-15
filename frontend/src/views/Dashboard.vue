<template>
  <div class="dashboard">
    <h2>仪表盘</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">12</div>
          <div class="stat-label">监控竞品</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">2,341</div>
          <div class="stat-label">情报条目</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">48</div>
          <div class="stat-label">分析报告</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">3</div>
          <div class="stat-label stat-warn">未读预警</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>情报趋势（近 30 天）</template>
          <div class="chart-placeholder">
            <el-icon :size="48"><TrendCharts /></el-icon>
            <p>图表区域 — 集成 ECharts 后展示</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>最新动态</template>
          <el-timeline>
            <el-timeline-item timestamp="2026-06-15" color="#409eff">
              竞品A 发布新版本 v3.2
            </el-timeline-item>
            <el-timeline-item timestamp="2026-06-14" color="#67c23a">
              竞品B 完成 C 轮融资
            </el-timeline-item>
            <el-timeline-item timestamp="2026-06-13" color="#e6a23c">
              竞品C 调整定价策略
            </el-timeline-item>
            <el-timeline-item timestamp="2026-06-12">
              竞品D 新增 AI 功能模块
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.dashboard { padding: 0 10px; }
.stat-row { margin-bottom: 20px; }
.stat-card { text-align: center; cursor: pointer; }
.stat-value { font-size: 32px; font-weight: bold; color: #409eff; }
.stat-label { font-size: 14px; color: #909399; margin-top: 8px; }
.stat-warn { color: #e6a23c; }
.chart-placeholder {
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  background: #fafafa;
  border-radius: 4px;
}
</style>
