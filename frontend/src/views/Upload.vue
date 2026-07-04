<template>
  <div class="upload-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>图片上传</span>
          <el-tag type="info">支持 jpg、png、bmp、tiff、webp 格式，单文件最大 50MB</el-tag>
        </div>
      </template>

      <!-- 上传区域 -->
      <el-upload
        ref="uploadRef"
        class="upload-dragger"
        drag
        multiple
        :auto-upload="false"
        :file-list="fileList"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        accept=".jpg,.jpeg,.png,.bmp,.tiff,.webp"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持批量上传，单次最多 1000 张
          </div>
        </template>
      </el-upload>

      <!-- 上传按钮 -->
      <div class="upload-actions">
        <el-button
          type="primary"
          size="large"
          :loading="uploading"
          :disabled="fileList.length === 0"
          @click="handleUpload"
        >
          <el-icon><Upload /></el-icon>
          开始上传 ({{ fileList.length }} 张)
        </el-button>
        <el-button size="large" @click="handleClear">清空列表</el-button>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploading" class="upload-progress">
        <el-progress
          :percentage="overallProgress"
          :status="overallProgress === 100 ? 'success' : ''"
        />
        <p class="progress-text">
          正在上传: {{ currentFile }} ({{ uploadedCount }}/{{ fileList.length }})
        </p>
      </div>
    </el-card>

    <!-- 上传结果 -->
    <el-card v-if="uploadResults.length > 0" shadow="hover" class="result-card">
      <template #header>
        <span>上传结果</span>
      </template>

      <el-table :data="uploadResults" stripe>
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'parsing' ? 'success' : 'danger'">
              {{ row.status === 'parsing' ? '上传成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="信息" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadInstance } from 'element-plus'
import { uploadApi } from '@/api'

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

const handleFileChange = (file: UploadFile) => {
  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp']
  if (file.raw && !allowedTypes.includes(file.raw.type)) {
    ElMessage.warning(`不支持的文件格式: ${file.name}`)
    fileList.value.pop()
    return
  }

  // 验证文件大小
  if (file.raw && file.raw.size > 50 * 1024 * 1024) {
    ElMessage.warning(`文件过大: ${file.name}`)
    fileList.value.pop()
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
.upload-page {
  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .upload-dragger {
    width: 100%;

    :deep(.el-upload-dragger) {
      width: 100%;
      height: 200px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
  }

  .upload-actions {
    margin-top: 20px;
    text-align: center;
  }

  .upload-progress {
    margin-top: 20px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 8px;

    .progress-text {
      margin-top: 10px;
      text-align: center;
      color: #606266;
    }
  }

  .result-card {
    margin-top: 20px;
  }
}
</style>
