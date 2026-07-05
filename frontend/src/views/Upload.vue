<template>
  <div class="upload-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="page-title">{{ t('image.upload') }}</h2>
        <p class="page-subtitle">{{ t('user.login') === 'Login' ? 'Support jpg, png, bmp, tiff, webp, max 50MB' : '支持 jpg、png、bmp、tiff、webp 格式，单文件最大 50MB' }}</p>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ fileList.length }}</span>
          <span class="stat-label">{{ t('user.login') === 'Login' ? 'Selected' : '已选择' }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ uploadedCount }}</span>
          <span class="stat-label">{{ t('user.login') === 'Login' ? 'Uploaded' : '已上传' }}</span>
        </div>
      </div>
    </div>

    <!-- 上传区域 -->
    <div class="upload-card">
      <el-upload
        ref="uploadRef"
        class="upload-dragger"
        drag
        multiple
        :auto-upload="false"
        v-model:file-list="fileList"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        accept=".jpg,.jpeg,.png,.bmp,.tiff,.webp"
      >
        <div class="upload-content">
          <div class="upload-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 15V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M17 8L12 3L7 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 3V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="upload-text">
            <p class="primary-text">{{ t('user.login') === 'Login' ? 'Drag files here, or' : '将文件拖到此处，或' }} <em>{{ t('user.login') === 'Login' ? 'click to upload' : '点击上传' }}</em></p>
            <p class="secondary-text">{{ t('user.login') === 'Login' ? 'Support batch upload, max 1000 files' : '支持批量上传，单次最多 1000 张' }}</p>
          </div>
        </div>
      </el-upload>

      <!-- 上传按钮 -->
      <div class="upload-actions">
        <button
          class="upload-btn primary"
          :disabled="fileList.length === 0 || uploading"
          @click="handleUpload"
        >
          <span v-if="uploading" class="btn-loading"></span>
          <span v-else class="btn-icon">↑</span>
          <span class="btn-text">{{ uploading ? (t('user.login') === 'Login' ? 'Uploading...' : '上传中...') : (t('user.login') === 'Login' ? 'Start Upload' : '开始上传') }}</span>
          <span class="btn-badge">{{ fileList.length }}</span>
        </button>
        <button class="upload-btn secondary" :disabled="fileList.length === 0 && uploadResults.length === 0" @click="handleClear">
          <span class="btn-icon">✕</span>
          <span class="btn-text">{{ t('user.login') === 'Login' ? 'Clear List' : '清空列表' }}</span>
        </button>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploading" class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: overallProgress + '%' }"></div>
        </div>
        <div class="progress-info">
          <span class="progress-text">正在上传: {{ currentFile }}</span>
          <span class="progress-count">{{ uploadedCount }}/{{ fileList.length }}</span>
        </div>
      </div>
    </div>

    <!-- 上传结果 -->
    <div v-if="uploadResults.length > 0" class="result-card">
      <div class="result-header">
        <h3 class="result-title">上传结果</h3>
        <div class="result-summary">
          <span class="success-count">成功: {{ uploadResults.filter(r => r.status === 'parsing').length }}</span>
          <span class="fail-count">失败: {{ uploadResults.filter(r => r.status !== 'parsing').length }}</span>
        </div>
      </div>

      <div class="result-list">
        <div v-for="(result, index) in uploadResults" :key="index" class="result-item">
          <div class="result-icon" :class="result.status === 'parsing' ? 'success' : 'fail'">
            <span v-if="result.status === 'parsing'">✓</span>
            <span v-else>✕</span>
          </div>
          <div class="result-content">
            <div class="result-filename">{{ result.filename }}</div>
            <div class="result-message">{{ result.message }}</div>
          </div>
          <div class="result-status" :class="result.status === 'parsing' ? 'success' : 'fail'">
            {{ result.status === 'parsing' ? '上传成功' : '失败' }}
          </div>
        </div>
      </div>

      <div v-if="successfulUploads > 0" class="next-actions">
        <span class="next-tip">上传成功 {{ successfulUploads }} 张，系统正在解析标签。</span>
        <button class="next-btn" @click="router.push('/images')">查看图片</button>
        <button class="next-btn secondary" @click="router.push('/review')">去审核</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadInstance } from 'element-plus'
import { uploadApi } from '@/api'
import { t } from '../utils/i18n'

const router = useRouter()
const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFile[]>([])
const uploading = ref(false)
const uploadedCount = ref(0)
const currentFile = ref('')
const uploadResults = ref<any[]>([])

const overallProgress = computed(() => {
  if (fileList.value.length === 0) return 0
  return Math.round((uploadedCount.value / fileList.value.length) * 100)
})
const successfulUploads = computed(() => uploadResults.value.filter(r => r.status === 'parsing').length)

const handleFileChange = (file: UploadFile) => {
  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp']
  if (file.raw && !allowedTypes.includes(file.raw.type)) {
    ElMessage.warning(`不支持的文件格式: ${file.name}`)
    // 移除无效文件
    const index = fileList.value.findIndex(f => f.uid === file.uid)
    if (index > -1) {
      fileList.value.splice(index, 1)
    }
    return
  }

  // 验证文件大小
  if (file.raw && file.raw.size > 50 * 1024 * 1024) {
    ElMessage.warning(`文件过大: ${file.name}`)
    // 移除无效文件
    const index = fileList.value.findIndex(f => f.uid === file.uid)
    if (index > -1) {
      fileList.value.splice(index, 1)
    }
    return
  }
}

const handleFileRemove = (file: UploadFile) => {
  const index = fileList.value.findIndex(f => f.uid === file.uid)
  if (index > -1) {
    fileList.value.splice(index, 1)
  }
}

const handleClear = () => {
  fileList.value = []
  uploadResults.value = []
  uploadedCount.value = 0
}

const handleUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  uploadedCount.value = 0
  uploadResults.value = []

  // 批量上传
  const files = fileList.value.map(f => f.raw!).filter(Boolean)

  try {
    const res: any = await uploadApi.uploadBatch(files)
    uploadResults.value = res.results || []
    uploadedCount.value = fileList.value.length

    ElMessage.success(`上传完成: 成功${res.success}张，失败${res.failed}张`)

    // 清空已上传的文件
    if (res.success > 0) {
      fileList.value = []
    }
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.upload-page {
  font-family: 'JetBrains Mono', monospace;
}

/* 页面标题 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.header-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #3b82f6;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

/* 上传卡片 */
.upload-card {
  background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 32px;
}

.upload-dragger {
  width: 100%;

  :deep(.el-upload) {
    width: 100%;
  }

  :deep(.el-upload-dragger) {
    width: 100%;
    height: 240px;
    background: #0f172a;
    border: 2px dashed #1e293b;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;

    &:hover {
      border-color: #3b82f6;
      background: #1e293b;
    }
  }
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-icon {
  width: 64px;
  height: 64px;
  color: #3b82f6;
}

.upload-text {
  text-align: center;
}

.primary-text {
  font-size: 16px;
  color: #f1f5f9;
  margin: 0 0 8px 0;

  em {
    color: #3b82f6;
    font-style: normal;
    cursor: pointer;
  }
}

.secondary-text {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

/* 上传按钮 */
.upload-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.upload-btn {
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

  &.primary {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: #fff;

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  &.secondary {
    background: #1e293b;
    color: #94a3b8;

    &:hover:not(:disabled) {
      background: #334155;
      color: #f1f5f9;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.next-actions {
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.next-tip {
  color: #94a3b8;
  font-size: 13px;
}

.next-btn {
  border: 1px solid #3b82f6;
  background: rgba(59, 130, 246, 0.12);
  color: #60a5fa;
  border-radius: 8px;
  padding: 9px 14px;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;

  &:hover {
    background: rgba(59, 130, 246, 0.22);
  }

  &.secondary {
    border-color: #10b981;
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;

    &:hover {
      background: rgba(16, 185, 129, 0.22);
    }
  }
}

.btn-icon {
  font-size: 16px;
}

.btn-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
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

/* 上传进度 */
.upload-progress {
  margin-top: 24px;
  padding: 20px;
  background: #0f172a;
  border-radius: 12px;
  border: 1px solid #1e293b;
}

.progress-bar {
  height: 8px;
  background: #1e293b;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.progress-text {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

.progress-count {
  font-size: 13px;
  color: #3b82f6;
  font-weight: 500;
}

/* 上传结果 */
.result-card {
  margin-top: 24px;
  background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 24px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.result-title {
  font-size: 18px;
  font-weight: 500;
  color: #f1f5f9;
  margin: 0;
}

.result-summary {
  display: flex;
  gap: 16px;
}

.success-count {
  font-size: 13px;
  color: #10b981;
}

.fail-count {
  font-size: 13px;
  color: #ef4444;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #0f172a;
  border-radius: 10px;
  border: 1px solid #1e293b;
}

.result-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;

  &.success {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  &.fail {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
}

.result-content {
  flex: 1;
}

.result-filename {
  font-size: 14px;
  color: #f1f5f9;
  margin-bottom: 4px;
}

.result-message {
  font-size: 12px;
  color: #64748b;
}

.result-status {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 6px;

  &.success {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  &.fail {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
}
</style>
