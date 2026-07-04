<template>
  <div class="image-detail" v-loading="loading">
    <el-page-header @back="router.back()">
      <template #content>
        <span>图片详情</span>
      </template>
    </el-page-header>

    <el-row :gutter="20" class="detail-content">
      <!-- 左侧：图片预览 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>图片预览</span>
          </template>
          <div class="image-preview">
            <el-image
              :src="`/uploads/temp/${image.stored_filename}`"
              fit="contain"
              :preview-src-list="[`/uploads/temp/${image.stored_filename}`]"
              class="preview-image"
            />
          </div>
          <div class="image-info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="文件名">{{ image.original_filename }}</el-descriptions-item>
              <el-descriptions-item label="UUID">{{ image.image_uuid }}</el-descriptions-item>
              <el-descriptions-item label="尺寸">{{ image.width }} × {{ image.height }}</el-descriptions-item>
              <el-descriptions-item label="大小">{{ formatSize(image.file_size) }}</el-descriptions-item>
              <el-descriptions-item label="格式">{{ image.file_format }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(image.status)">{{ getStatusLabel(image.status) }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：标签信息 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>标签信息</span>
              <el-tag :type="label.source === 'auto' ? 'info' : 'success'">
                {{ label.source === 'auto' ? '自动识别' : '人工修正' }}
              </el-tag>
            </div>
          </template>

          <el-form :model="label" label-width="100px" size="small">
            <!-- 时间维度 -->
            <el-divider content-position="left">时间维度</el-divider>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item label="季节">
                  <el-select v-model="label.season" clearable>
                    <el-option v-for="s in enums.seasons" :key="s" :label="s" :value="s" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="时段">
                  <el-select v-model="label.time_period" clearable>
                    <el-option v-for="t in enums.time_periods" :key="t" :label="t" :value="t" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="工作日">
                  <el-select v-model="label.day_type" clearable>
                    <el-option v-for="d in enums.day_types" :key="d" :label="d" :value="d" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 环境天气 -->
            <el-divider content-position="left">环境天气</el-divider>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item label="天气">
                  <el-select v-model="label.weather" clearable>
                    <el-option v-for="w in enums.weather_types" :key="w" :label="w" :value="w" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="温度">
                  <el-input-number v-model="label.temperature" :min="-50" :max="60" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="光照">
                  <el-select v-model="label.light" clearable>
                    <el-option v-for="l in enums.light_conditions" :key="l" :label="l" :value="l" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 拍摄维度 -->
            <el-divider content-position="left">拍摄维度</el-divider>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item label="拍摄角度">
                  <el-select v-model="label.shoot_angle" clearable>
                    <el-option v-for="a in enums.shoot_angles" :key="a" :label="a" :value="a" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="景别">
                  <el-select v-model="label.scene_scale" clearable>
                    <el-option v-for="s in enums.scene_scales" :key="s" :label="s" :value="s" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="清晰度">
                  <el-select v-model="label.clarity" clearable>
                    <el-option v-for="c in enums.clarity_levels" :key="c" :label="c" :value="c" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 场景设备 -->
            <el-divider content-position="left">场景设备</el-divider>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item label="场景类型">
                  <el-select v-model="label.scene_type" clearable>
                    <el-option v-for="s in enums.scene_types" :key="s" :label="s" :value="s" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="设备类型">
                  <el-select v-model="label.device_type" clearable>
                    <el-option v-for="d in enums.device_types" :key="d" :label="d" :value="d" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="曝光">
                  <el-select v-model="label.exposure" clearable>
                    <el-option v-for="e in enums.exposure_levels" :key="e" :label="e" :value="e" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 地理位置 -->
            <el-divider content-position="left">地理位置</el-divider>
            <el-row :gutter="10">
              <el-col :span="8">
                <el-form-item label="省">
                  <el-input v-model="label.province" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="市">
                  <el-input v-model="label.city" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="区">
                  <el-input v-model="label.district" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <div class="form-actions">
            <el-button type="primary" :loading="saving" @click="handleSave">
              保存修改
            </el-button>
            <el-button @click="loadData">重置</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
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

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    parsing: 'warning',
    parsed: 'info',
    checked: 'success',
    discarded: 'danger',
  }
  return map[status] || 'info'
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
</script>

<style scoped lang="scss">
.image-detail {
  .detail-content {
    margin-top: 20px;
  }

  .image-preview {
    display: flex;
    justify-content: center;
    background: #f5f7fa;
    border-radius: 8px;
    padding: 20px;

    .preview-image {
      max-height: 400px;
    }
  }

  .image-info {
    margin-top: 20px;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .form-actions {
    margin-top: 20px;
    text-align: center;
  }
}
</style>
