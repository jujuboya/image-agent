<template>
  <div class="image-detail" v-loading="loading">
    <!-- 页面标题 -->
    <div class="page-header">
      <button class="back-btn" @click="router.back()">
        <span class="btn-icon">←</span>
        <span class="btn-text">返回</span>
      </button>
      <div class="header-content">
        <h2 class="page-title">图片详情</h2>
        <p class="page-subtitle">{{ image.original_filename }}</p>
      </div>
      <div class="header-actions">
        <button class="action-btn primary" :disabled="saving" @click="handleSave">
          <span v-if="saving" class="btn-loading"></span>
          <span v-else class="btn-icon">💾</span>
          <span class="btn-text">{{ saving ? '保存中...' : '保存修改' }}</span>
        </button>
      </div>
    </div>

    <div class="detail-content">
      <!-- 左侧：图片预览 -->
      <div class="preview-section">
        <div class="preview-card">
          <div class="card-header">
            <div class="card-title">
              <span class="title-dot"></span>
              <span>图片预览</span>
            </div>
          </div>
          <div class="image-preview">
            <el-image
              v-if="image.stored_filename"
              :src="getImageUrl(image.file_path)"
              fit="contain"
              :preview-src-list="[getImageUrl(image.file_path)]"
              class="preview-image"
            />
            <div v-else class="preview-placeholder">暂无图片</div>
          </div>
          <div class="image-info">
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">文件名</span>
                <span class="info-value">{{ image.original_filename }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">UUID</span>
                <span class="info-value uuid">{{ image.image_uuid }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">尺寸</span>
                <span class="info-value">{{ image.width }} × {{ image.height }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">大小</span>
                <span class="info-value">{{ formatSize(image.file_size) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">格式</span>
                <span class="info-value">{{ image.file_format }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">状态</span>
                <span class="status-tag" :class="image.status">
                  {{ getStatusLabel(image.status) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：标签信息 -->
      <div class="label-section">
        <div class="label-card">
          <div class="card-header">
            <div class="card-title">
              <span class="title-dot"></span>
              <span>标签信息</span>
            </div>
            <span class="source-tag" :class="label.source">
              {{ label.source === 'auto' ? '自动识别' : '人工修正' }}
            </span>
          </div>

          <div class="label-form">
            <!-- 时间维度 -->
            <div class="form-section">
              <div class="section-title">
                <span class="section-icon">⏱</span>
                <span>时间维度</span>
              </div>
              <div class="form-grid">
                <div class="form-item">
                  <label class="form-label">季节</label>
                  <el-select v-model="label.season" clearable>
                    <el-option v-for="s in enums.seasons" :key="s" :label="s" :value="s" />
                  </el-select>
                </div>
                <div class="form-item">
                  <label class="form-label">时段</label>
                  <el-select v-model="label.time_period" clearable>
                    <el-option v-for="t in enums.time_periods" :key="t" :label="t" :value="t" />
                  </el-select>
                </div>
                <div class="form-item">
                  <label class="form-label">工作日</label>
                  <el-select v-model="label.day_type" clearable>
                    <el-option v-for="d in enums.day_types" :key="d" :label="d" :value="d" />
                  </el-select>
                </div>
              </div>
            </div>

            <!-- 环境天气 -->
            <div class="form-section">
              <div class="section-title">
                <span class="section-icon">🌤</span>
                <span>环境天气</span>
              </div>
              <div class="form-grid">
                <div class="form-item">
                  <label class="form-label">天气</label>
                  <el-select v-model="label.weather" clearable>
                    <el-option v-for="w in enums.weather_types" :key="w" :label="w" :value="w" />
                  </el-select>
                </div>
                <div class="form-item">
                  <label class="form-label">温度</label>
                  <el-input-number v-model="label.temperature" :min="-50" :max="60" />
                </div>
                <div class="form-item">
                  <label class="form-label">光照</label>
                  <el-select v-model="label.light" clearable>
                    <el-option v-for="l in enums.light_conditions" :key="l" :label="l" :value="l" />
                  </el-select>
                </div>
              </div>
            </div>

            <!-- 拍摄维度 -->
            <div class="form-section">
              <div class="section-title">
                <span class="section-icon">📷</span>
                <span>拍摄维度</span>
              </div>
              <div class="form-grid">
                <div class="form-item">
                  <label class="form-label">拍摄角度</label>
                  <el-select v-model="label.shoot_angle" clearable>
                    <el-option v-for="a in enums.shoot_angles" :key="a" :label="a" :value="a" />
                  </el-select>
                </div>
                <div class="form-item">
                  <label class="form-label">景别</label>
                  <el-select v-model="label.scene_scale" clearable>
                    <el-option v-for="s in enums.scene_scales" :key="s" :label="s" :value="s" />
                  </el-select>
                </div>
                <div class="form-item">
                  <label class="form-label">清晰度</label>
                  <el-select v-model="label.clarity" clearable>
                    <el-option v-for="c in enums.clarity_levels" :key="c" :label="c" :value="c" />
                  </el-select>
                </div>
              </div>
            </div>

            <!-- 场景设备 -->
            <div class="form-section">
              <div class="section-title">
                <span class="section-icon">🏞</span>
                <span>场景设备</span>
              </div>
              <div class="form-grid">
                <div class="form-item">
                  <label class="form-label">场景类型</label>
                  <el-select v-model="label.scene_type" clearable>
                    <el-option v-for="s in enums.scene_types" :key="s" :label="s" :value="s" />
                  </el-select>
                </div>
                <div class="form-item">
                  <label class="form-label">设备类型</label>
                  <el-select v-model="label.device_type" clearable>
                    <el-option v-for="d in enums.device_types" :key="d" :label="d" :value="d" />
                  </el-select>
                </div>
                <div class="form-item">
                  <label class="form-label">曝光</label>
                  <el-select v-model="label.exposure" clearable>
                    <el-option v-for="e in enums.exposure_levels" :key="e" :label="e" :value="e" />
                  </el-select>
                </div>
              </div>
            </div>

            <!-- 地理位置 -->
            <div class="form-section">
              <div class="section-title">
                <span class="section-icon">📍</span>
                <span>地理位置</span>
              </div>
              <div class="form-grid">
                <div class="form-item">
                  <label class="form-label">省</label>
                  <el-input v-model="label.province" />
                </div>
                <div class="form-item">
                  <label class="form-label">市</label>
                  <el-input v-model="label.city" />
                </div>
                <div class="form-item">
                  <label class="form-label">区</label>
                  <el-input v-model="label.district" />
                </div>
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button class="save-btn" :disabled="saving" @click="handleSave">
              <span v-if="saving" class="btn-loading"></span>
              <span v-else class="btn-icon">💾</span>
              <span class="btn-text">{{ saving ? '保存中...' : '保存修改' }}</span>
            </button>
            <button class="reset-btn" @click="loadData">
              <span class="btn-icon">↻</span>
              <span class="btn-text">重置</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { imageApi, labelApi } from '@/api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const imageId = Number(route.params.id)

const image = ref<any>({})
const label = ref<any>({})
const enums = ref<any>({})

onMounted(() => {
  loadData()
  loadEnums()
})

const loadData = async () => {
  loading.value = true
  try {
    const [imageRes, labelRes]: any = await Promise.all([
      imageApi.getDetail(imageId),
      labelApi.getLabel(imageId),
    ])
    image.value = imageRes
    label.value = labelRes
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
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

const handleSave = async () => {
  saving.value = true
  try {
    await labelApi.update({
      image_id: imageId,
      ...label.value,
    })
    ElMessage.success('保存成功')
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    saving.value = false
  }
}

const formatSize = (bytes: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    uploading: '上传中',
    parsing: '解析中',
    parsed: '已解析',
    checked: '已通过',
    discarded: '已废弃',
  }
  return map[status] || status
}

const getImageUrl = (filePath: string) => {
  if (!filePath) return ''
  // 将反斜杠替换为正斜杠
  return '/' + filePath.replace(/\\/g, '/')
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.image-detail {
  font-family: 'JetBrains Mono', monospace;
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #1e293b;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;

  &:hover {
    background: #334155;
    color: #f1f5f9;
  }
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;

  &.primary {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: #fff;

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
}

.btn-loading {
  width: 16px;
  height: 16px;
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

/* 详情内容 */
.detail-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.preview-section,
.label-section {
  min-width: 0;
}

.preview-card,
.label-card {
  background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 24px;
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
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

/* 图片预览 */
.image-preview {
  background: #0f172a;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 20px;
  min-height: 300px;
}

.preview-image {
  max-height: 400px;
  border-radius: 8px;
}

.preview-placeholder {
  color: #64748b;
  font-size: 14px;
}

.image-info {
  margin-top: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #0f172a;
  border-radius: 8px;
  border: 1px solid #1e293b;
}

.info-label {
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.info-value {
  font-size: 13px;
  color: #f1f5f9;
  font-weight: 500;

  &.uuid {
    font-size: 11px;
    color: #94a3b8;
  }
}

.status-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;

  &.parsing {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }

  &.parsed {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  &.checked {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  &.discarded {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
}

/* 标签信息 */
.source-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;

  &.auto {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  &.manual {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }
}

.label-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section {
  padding: 16px;
  background: #0f172a;
  border-radius: 12px;
  border: 1px solid #1e293b;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #f1f5f9;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

:deep(.el-select) {
  .el-input__wrapper {
    background: #1e293b;
    border: 1px solid #334155;
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

:deep(.el-input-number) {
  .el-input__wrapper {
    background: #1e293b;
    border: 1px solid #334155;
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

:deep(.el-input__wrapper) {
  background: #1e293b;
  border: 1px solid #334155;
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

/* 表单操作 */
.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #1e293b;
}

.save-btn,
.reset-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;
}

.save-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.reset-btn {
  background: #1e293b;
  color: #94a3b8;

  &:hover {
    background: #334155;
    color: #f1f5f9;
  }
}
</style>
