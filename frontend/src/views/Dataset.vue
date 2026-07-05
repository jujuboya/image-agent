<template>
  <div class="dataset-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="page-title">{{ t('nav.dataset') }}</h2>
        <p class="page-subtitle">{{ t('user.login') === 'Login' ? 'Manage and export reviewed datasets' : '管理和导出已审核通过的数据集' }}</p>
      </div>
    </div>

    <!-- 数据集统计 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)">
          <el-icon size="24"><Picture /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-value">{{ stats.total_images || 0 }}</div>
          <div class="card-label">{{ t('user.login') === 'Login' ? 'Approved Images' : '已通过图片' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%)">
          <el-icon size="24"><FolderOpened /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-value">{{ versions.length }}</div>
          <div class="card-label">{{ t('user.login') === 'Login' ? 'Versions' : '版本数量' }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%)">
          <el-icon size="24"><DataAnalysis /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-value">{{ Object.keys(stats.scene_distribution || {}).length }}</div>
          <div class="card-label">{{ t('user.login') === 'Login' ? 'Scene Categories' : '场景类别' }}</div>
        </div>
      </div>
    </div>

    <!-- 导出操作 -->
    <div class="export-card">
      <div class="card-header">
        <div class="card-title">
          <span class="title-dot"></span>
          <span>{{ t('user.login') === 'Login' ? 'Dataset Export' : '数据集导出' }}</span>
        </div>
      </div>

      <div class="export-form">
        <div class="form-group">
          <label class="form-label">{{ t('user.login') === 'Login' ? 'Export Format' : '导出格式' }}</label>
          <div class="format-selector">
            <button
              v-for="format in formats"
              :key="format.value"
              class="format-btn"
              :class="{ active: exportForm.format === format.value }"
              @click="exportForm.format = format.value"
            >
              <span class="format-icon">{{ format.icon }}</span>
              <span class="format-name">{{ format.label }}</span>
            </button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ t('user.login') === 'Login' ? 'Version Name' : '版本名称' }}</label>
          <div class="form-input">
            <el-input v-model="exportForm.version_name" :placeholder="t('user.login') === 'Login' ? 'Auto generate if empty' : '留空自动生成'" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ t('user.login') === 'Login' ? 'Filters' : '筛选条件' }}</label>
          <div class="filter-row">
            <div class="filter-item">
              <el-select v-model="exportForm.filters.scene_type" clearable placeholder="场景类型">
                <el-option v-for="s in enums.scene_types" :key="s" :label="s" :value="s" />
              </el-select>
            </div>
            <div class="filter-item">
              <el-select v-model="exportForm.filters.weather" clearable placeholder="天气">
                <el-option v-for="w in enums.weather_types" :key="w" :label="w" :value="w" />
              </el-select>
            </div>
            <div class="filter-item">
              <el-select v-model="exportForm.filters.season" clearable placeholder="季节">
                <el-option v-for="s in enums.seasons" :key="s" :label="s" :value="s" />
              </el-select>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button class="export-btn" :disabled="exporting" @click="handleExport">
            <span v-if="exporting" class="btn-loading"></span>
            <span v-else class="btn-icon">↓</span>
            <span class="btn-text">{{ exporting ? (t('user.login') === 'Login' ? 'Exporting...' : '导出中...') : (t('user.login') === 'Login' ? 'Export Dataset' : '导出数据集') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 版本历史 -->
    <div class="version-card">
      <div class="card-header">
        <div class="card-title">
          <span class="title-dot"></span>
          <span>{{ t('user.login') === 'Login' ? 'Version History' : '版本历史' }}</span>
        </div>
      </div>

      <el-table :data="versions" class="custom-table">
        <el-table-column prop="version_name" :label="t('user.login') === 'Login' ? 'Version Name' : '版本名称'" />
        <el-table-column prop="version_code" :label="t('user.login') === 'Login' ? 'Version Code' : '版本号'" />
        <el-table-column prop="total_images" :label="t('user.login') === 'Login' ? 'Images' : '图片数量'" />
        <el-table-column prop="export_format" :label="t('user.login') === 'Login' ? 'Format' : '导出格式'">
          <template #default="{ row }">
            <span v-if="row.export_format" class="format-tag">{{ row.export_format.toUpperCase() }}</span>
            <span v-else class="no-format">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="t('image.status')">
          <template #default="{ row }">
            <span class="status-tag" :class="row.status">
              {{ row.status === 'ready' ? (t('user.login') === 'Login' ? 'Ready' : '就绪') : row.status }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="t('image.createdAt')">
          <template #default="{ row }">
            <span class="time-text">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { datasetApi, labelApi } from '@/api'
import dayjs from 'dayjs'
import { t } from '../utils/i18n'

const exporting = ref(false)
const versions = ref<any[]>([])
const stats = ref<any>({})
const enums = ref<any>({})

const formats = [
  { value: 'yolo', label: 'YOLO', icon: '🎯' },
  { value: 'coco', label: 'COCO', icon: '📦' },
  { value: 'voc', label: 'VOC', icon: '📋' },
  { value: 'json', label: 'JSON', icon: '📄' },
  { value: 'csv', label: 'CSV', icon: '📊' },
]

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
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.dataset-page {
  font-family: 'JetBrains Mono', monospace;
}

/* 页面标题 */
.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

/* 统计卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
    border-color: #3b82f6;
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
  color: #f1f5f9;
  line-height: 1;
  margin-bottom: 4px;
}

.card-label {
  font-size: 13px;
  color: #64748b;
}

/* 导出操作 */
.export-card,
.version-card {
  background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.card-header {
  margin-bottom: 24px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 500;
  color: #f1f5f9;
}

.title-dot {
  width: 8px;
  height: 8px;
  background: #3b82f6;
  border-radius: 50%;
}

.export-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #94a3b8;
}

.format-selector {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.format-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 24px;
  background: #0f172a;
  border: 2px solid #1e293b;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;

  &:hover {
    border-color: #3b82f6;
    background: #1e293b;
  }

  &.active {
    border-color: #3b82f6;
    background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%);
  }
}

.format-icon {
  font-size: 24px;
}

.format-name {
  font-size: 13px;
  font-weight: 500;
  color: #f1f5f9;
}

.form-input {
  max-width: 400px;

  :deep(.el-input__wrapper) {
    background: #0f172a;
    border: 1px solid #1e293b;
    box-shadow: none;

    &:hover {
      border-color: #3b82f6;
    }

    &.is-focus {
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
  }

  :deep(.el-input__inner) {
    color: #f1f5f9;
  }
}

.filter-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-item {
  min-width: 200px;

  :deep(.el-select) {
    .el-input__wrapper {
      background: #0f172a;
      border: 1px solid #1e293b;
      box-shadow: none;

      &:hover {
        border-color: #3b82f6;
      }

      &.is-focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
      }
    }

    .el-input__inner {
      color: #f1f5f9;
    }
  }
}

.form-actions {
  margin-top: 8px;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 28px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.btn-icon {
  font-size: 18px;
}

.btn-loading {
  width: 18px;
  height: 18px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 版本历史 */
.custom-table {
  :deep(.el-table__header-wrapper) {
    th {
      background: #0f172a;
      color: #94a3b8;
      font-weight: 500;
      border-bottom: 1px solid #1e293b;
    }
  }

  :deep(.el-table__body-wrapper) {
    tr {
      background: transparent;

      &:hover {
        background: #1e293b;
      }

      td {
        border-bottom: 1px solid #1e293b;
        color: #f1f5f9;
      }
    }
  }
}

.format-tag {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.no-format {
  color: #64748b;
}

.status-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;

  &.ready {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  &.creating {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }

  &.exported {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  &.archived {
    background: rgba(100, 116, 139, 0.1);
    color: #64748b;
  }
}

.time-text {
  font-size: 13px;
  color: #94a3b8;
}
</style>
