<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div v-for="(stat, index) in statCards" :key="index" class="stat-card">
        <div class="card-icon" :style="{ background: stat.gradient }">
          <el-icon size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-value">{{ stat.value }}</div>
          <div class="card-label">{{ stat.label }}</div>
        </div>
        <div class="card-trend" :class="stat.trendType">
          <el-icon><component :is="stat.trendIcon" /></el-icon>
          <span>{{ stat.trend }}</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="chart-section">
      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">
            <span class="title-dot"></span>
            <span>场景分布</span>
          </div>
          <div class="chart-actions">
            <el-button size="small" text>本周</el-button>
            <el-button size="small" text type="primary">本月</el-button>
            <el-button size="small" text>本年</el-button>
          </div>
        </div>
        <div ref="sceneChartRef" class="chart-container"></div>
      </div>

      <div class="chart-card">
        <div class="chart-header">
          <div class="chart-title">
            <span class="title-dot"></span>
            <span>天气分布</span>
          </div>
          <div class="chart-actions">
            <el-button size="small" text>本周</el-button>
            <el-button size="small" text type="primary">本月</el-button>
            <el-button size="small" text>本年</el-button>
          </div>
        </div>
        <div ref="weatherChartRef" class="chart-container"></div>
      </div>
    </div>

    <!-- 系统信息 -->
    <div class="system-section">
      <div class="system-card">
        <div class="card-header">
          <div class="chart-title">
            <span class="title-dot"></span>
            <span>系统信息</span>
          </div>
        </div>
        <div class="system-info-grid">
          <div class="info-item">
            <div class="info-icon">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="info-content">
              <div class="info-label">今日上传</div>
              <div class="info-value">{{ stats.today_upload || 0 }} <span class="info-unit">张</span></div>
            </div>
          </div>
          <div class="info-item">
            <div class="info-icon">
              <el-icon><InfoFilled /></el-icon>
            </div>
            <div class="info-content">
              <div class="info-label">系统版本</div>
              <div class="info-value">v1.0.0</div>
            </div>
          </div>
          <div class="info-item">
            <div class="info-icon">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="info-content">
              <div class="info-label">系统状态</div>
              <div class="info-value status-success">运行中</div>
            </div>
          </div>
          <div class="info-item">
            <div class="info-icon">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="info-content">
              <div class="info-label">运行时间</div>
              <div class="info-value">12 <span class="info-unit">小时</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="system-card">
        <div class="card-header">
          <div class="chart-title">
            <span class="title-dot"></span>
            <span>最近活动</span>
          </div>
          <el-button size="small" text type="primary">查看全部</el-button>
        </div>
        <div class="activity-list">
          <div v-for="(activity, index) in recentActivities" :key="index" class="activity-item">
            <div class="activity-dot" :class="activity.type"></div>
            <div class="activity-content">
              <div class="activity-text">{{ activity.text }}</div>
              <div class="activity-time">{{ activity.time }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { imageApi, datasetApi } from '@/api'

const stats = ref<any>({})
const datasetStats = ref<any>({})
const sceneChartRef = ref<HTMLElement>()
const weatherChartRef = ref<HTMLElement>()

const statCards = ref([
  {
    icon: 'Picture',
    label: '总图片数',
    value: 0,
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    trend: '+12%',
    trendType: 'success',
    trendIcon: 'Top',
  },
  {
    icon: 'Checked',
    label: '已通过',
    value: 0,
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    trend: '+8%',
    trendType: 'success',
    trendIcon: 'Top',
  },
  {
    icon: 'Loading',
    label: '解析中',
    value: 0,
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    trend: '-5%',
    trendType: 'danger',
    trendIcon: 'Bottom',
  },
  {
    icon: 'Delete',
    label: '已废弃',
    value: 0,
    gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    trend: '+2%',
    trendType: 'warning',
    trendIcon: 'Top',
  },
])

const recentActivities = ref([
  { text: '上传了 15 张图片', time: '2 分钟前', type: 'upload' },
  { text: '审核通过了 8 张图片', time: '15 分钟前', type: 'check' },
  { text: '导出了 YOLO 格式数据集', time: '1 小时前', type: 'export' },
  { text: '新增了 3 个标签', time: '2 小时前', type: 'label' },
  { text: '系统备份完成', time: '3 小时前', type: 'system' },
])

onMounted(async () => {
  await loadData()
  await nextTick()
  initCharts()
})

const loadData = async () => {
  try {
    const [imageStatsRes, datasetStatsRes]: any = await Promise.all([
      imageApi.getStats(),
      datasetApi.getStats(),
    ])
    stats.value = imageStatsRes
    datasetStats.value = datasetStatsRes

    // 更新统计卡片
    statCards.value[0].value = imageStatsRes.total || 0
    statCards.value[1].value = imageStatsRes.status_stats?.checked || 0
    statCards.value[2].value = imageStatsRes.status_stats?.parsing || 0
    statCards.value[3].value = imageStatsRes.status_stats?.discarded || 0
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const initCharts = () => {
  // 场景分布图
  if (sceneChartRef.value && datasetStats.value.scene_distribution) {
    const sceneChart = echarts.init(sceneChartRef.value)
    const sceneData = Object.entries(datasetStats.value.scene_distribution).map(
      ([name, value]) => ({ name, value })
    )

    sceneChart.setOption({
      tooltip: {
        trigger: 'item',
        backgroundColor: 'var(--bg-secondary)',
        borderColor: 'var(--border-color)',
        textStyle: {
          color: 'var(--text-primary)',
          fontFamily: 'JetBrains Mono',
        },
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: {
          color: 'var(--text-secondary)',
          fontFamily: 'JetBrains Mono',
        },
      },
      series: [
        {
          name: '场景分布',
          type: 'pie',
          radius: ['45%', '75%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#0a0e17',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
              color: '#f1f5f9',
            },
          },
          labelLine: {
            show: false,
          },
          data: sceneData,
          color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'],
        },
      ],
    })
  }

  // 天气分布图
  if (weatherChartRef.value && datasetStats.value.weather_distribution) {
    const weatherChart = echarts.init(weatherChartRef.value)
    const weatherData = Object.entries(datasetStats.value.weather_distribution).map(
      ([name, value]) => ({ name, value })
    )

    weatherChart.setOption({
      tooltip: {
        trigger: 'item',
        backgroundColor: 'var(--bg-secondary)',
        borderColor: 'var(--border-color)',
        textStyle: {
          color: 'var(--text-primary)',
          fontFamily: 'JetBrains Mono',
        },
      },
      legend: {
        orient: 'vertical',
        right: '5%',
        top: 'center',
        textStyle: {
          color: 'var(--text-secondary)',
          fontFamily: 'JetBrains Mono',
        },
      },
      series: [
        {
          name: '天气分布',
          type: 'pie',
          radius: ['45%', '75%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#0a0e17',
            borderWidth: 2,
          },
          label: {
            show: false,
            position: 'center',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
              color: '#f1f5f9',
            },
          },
          labelLine: {
            show: false,
          },
          data: weatherData,
          color: ['#f59e0b', '#94a3b8', '#64748b', '#3b82f6', '#8b5cf6'],
        },
      ],
    })
  }
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.dashboard {
  font-family: 'JetBrains Mono', monospace;
}

/* 统计卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
    border-color: var(--border-hover);
  }
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.card-label {
  font-size: 13px;
  color: var(--text-tertiary);
}

.card-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;

  &.success {
    color: var(--success-color);
    background: rgba(16, 185, 129, 0.1);
  }

  &.danger {
    color: var(--danger-color);
    background: rgba(239, 68, 68, 0.1);
  }

  &.warning {
    color: var(--warning-color);
    background: rgba(245, 158, 11, 0.1);
  }

  .el-icon {
    font-size: 14px;
  }
}

/* 图表区域 */
.chart-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

.title-dot {
  width: 8px;
  height: 8px;
  background: var(--accent-color);
  border-radius: 50%;
}

.chart-actions {
  display: flex;
  gap: 4px;

  .el-button {
    color: var(--text-tertiary);
    font-size: 12px;

    &.el-button--primary {
      color: var(--accent-color);
    }
  }
}

.chart-container {
  height: 300px;
}

/* 系统信息 */
.system-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.system-card {
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.system-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.info-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #1e3a5f 0%, var(--bg-secondary) 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-color);
  font-size: 20px;
}

.info-content {
  flex: 1;
}

.info-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.info-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);

  &.status-success {
    color: var(--success-color);
  }

  .info-unit {
    font-size: 12px;
    font-weight: 400;
    color: var(--text-tertiary);
  }
}

/* 最近活动 */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;

  &:hover {
    border-color: var(--border-hover);
  }
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;

  &.upload {
    background: #3b82f6;
  }

  &.check {
    background: #10b981;
  }

  &.export {
    background: #f59e0b;
  }

  &.label {
    background: #8b5cf6;
  }

  &.system {
    background: #64748b;
  }
}

.activity-content {
  flex: 1;
}

.activity-text {
  font-size: 13px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.activity-time {
  font-size: 11px;
  color: var(--text-tertiary);
}
</style>
