<template>
  <div class="dataset-page">
    <!-- 数据集统计 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-item">
            <el-icon size="40" color="#409eff"><Picture /></el-icon>
            <div>
              <div class="stat-value">{{ stats.total_images || 0 }}</div>
              <div class="stat-label">已通过图片</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-item">
            <el-icon size="40" color="#67c23a"><FolderOpened /></el-icon>
            <div>
              <div class="stat-value">{{ versions.length }}</div>
              <div class="stat-label">版本数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-item">
            <el-icon size="40" color="#e6a23c"><DataAnalysis /></el-icon>
            <div>
              <div class="stat-value">{{ Object.keys(stats.scene_distribution || {}).length }}</div>
              <div class="stat-label">场景类别</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 导出操作 -->
    <el-card shadow="hover" class="export-card">
      <template #header>
        <span>数据集导出</span>
      </template>

      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportForm.format">
            <el-radio-button label="yolo">YOLO</el-radio-button>
            <el-radio-button label="coco">COCO</el-radio-button>
            <el-radio-button label="voc">VOC</el-radio-button>
            <el-radio-button label="json">JSON</el-radio-button>
            <el-radio-button label="csv">CSV</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="版本名称">
          <el-input v-model="exportForm.version_name" placeholder="留空自动生成" />
        </el-form-item>

        <el-form-item label="筛选条件">
          <el-row :gutter="10">
            <el-col :span="8">
              <el-select v-model="exportForm.filters.scene_type" clearable placeholder="场景类型">
                <el-option v-for="s in enums.scene_types" :key="s" :label="s" :value="s" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-select v-model="exportForm.filters.weather" clearable placeholder="天气">
                <el-option v-for="w in enums.weather_types" :key="w" :label="w" :value="w" />
              </el-select>
            </el-col>
            <el-col :span="8">
              <el-select v-model="exportForm.filters.season" clearable placeholder="季节">
                <el-option v-for="s in enums.seasons" :key="s" :label="s" :value="s" />
              </el-select>
            </el-col>
          </el-row>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="exporting"
            @click="handleExport"
          >
            <el-icon><Download /></el-icon>
            导出数据集
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 版本历史 -->
    <el-card shadow="hover">
      <template #header>
        <span>版本历史</span>
      </template>

      <el-table :data="versions" stripe>
        <el-table-column prop="version_name" label="版本名称" />
        <el-table-column prop="version_code" label="版本号" />
        <el-table-column prop="total_images" label="图片数量" />
        <el-table-column prop="export_format" label="导出格式">
          <template #default="{ row }">
            <el-tag v-if="row.export_format">{{ row.export_format.toUpperCase() }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ready' ? 'success' : 'info'">
              {{ row.status === 'ready' ? '就绪' : row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { datasetApi, labelApi } from '@/api'
import dayjs from 'dayjs'

const exporting = ref(false)
const versions = ref<any[]>([])
const stats = ref<any>({})
const enums = ref<any>({})

const exportForm = reactive({
  format: 'yolo',
  version_name: '',
  filters: {
    scene_type: '',
    weather: '',
    season: '',
  },
})

onMounted(() => {
  loadData()
  loadEnums()
})

const loadData = async () => {
  try {
    const [versionsRes, statsRes]: any = await Promise.all([
      datasetApi.getVersions(),
      datasetApi.getStats(),
    ])
    versions.value = versionsRes || []
    stats.value = statsRes || {}
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const loadEnums = async () => {
  try {
    const res: any = await labelApi.getEnums()
    enums.value = res
  } catch (error) {
    console.error('加载枚举失败:', error)
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const filters: any = {}
    if (exportForm.filters.scene_type) filters.scene_type = exportForm.filters.scene_type
    if (exportForm.filters.weather) filters.weather = exportForm.filters.weather
    if (exportForm.filters.season) filters.season = exportForm.filters.season

    const response: any = await datasetApi.export({
      format: exportForm.format,
      filters: Object.keys(filters).length > 0 ? filters : undefined,
      version_name: exportForm.version_name || undefined,
    })

    // 下载文件
    const blob = new Blob([response])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `dataset_${exportForm.format}_${dayjs().format('YYYYMMDD')}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
    loadData()
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}
</script>

<style scoped lang="scss">
.dataset-page {
  .stat-row {
    margin-bottom: 20px;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 20px;

    .stat-value {
      font-size: 28px;
      font-weight: 600;
      color: #303133;
    }

    .stat-label {
      font-size: 14px;
      color: #909399;
    }
  }

  .export-card {
    margin-bottom: 20px;
  }
}
</style>
