<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #409eff">
            <el-icon size="32"><Picture /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total || 0 }}</div>
            <div class="stat-label">总图片数</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #67c23a">
            <el-icon size="32"><Checked /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.status_stats?.checked || 0 }}</div>
            <div class="stat-label">已通过</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e6a23c">
            <el-icon size="32"><Loading /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.status_stats?.parsing || 0 }}</div>
            <div class="stat-label">解析中</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f56c6c">
            <el-icon size="32"><Delete /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.status_stats?.discarded || 0 }}</div>
            <div class="stat-label">已废弃</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>场景分布</span>
          </template>
          <div ref="sceneChartRef" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>天气分布</span>
          </template>
          <div ref="weatherChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 今日上传 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>系统信息</span>
            </div>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="今日上传">
              <el-tag type="success">{{ stats.today_upload || 0 }} 张</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="系统版本">
              <el-tag>v1.0.0</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="系统状态">
              <el-tag type="success">运行中</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
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
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [
        {
          name: '场景分布',
          type: 'pie',
          radius: '50%',
          data: sceneData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
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
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [
        {
          name: '天气分布',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: { show: false, position: 'center' },
          emphasis: {
            label: { show: true, fontSize: 20, fontWeight: 'bold' },
          },
          labelLine: { show: false },
          data: weatherData,
        },
      ],
    })
  }
}
</script>

<style scoped lang="scss">
.dashboard {
  .stat-cards {
    margin-bottom: 20px;
  }

  .stat-card {
    :deep(.el-card__body) {
      display: flex;
      align-items: center;
      gap: 20px;
      padding: 20px;
    }

    .stat-icon {
      width: 64px;
      height: 64px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }

    .stat-info {
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #303133;
      }

      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-top: 4px;
      }
    }
  }

  .chart-row {
    margin-bottom: 20px;
  }

  .chart-container {
    height: 300px;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
}
</style>
