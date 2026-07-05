<template>
  <div class="review-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="page-title">{{ t('nav.review') }}</h2>
        <p class="page-subtitle">{{ t('user.login') === 'Login' ? 'Review AI labels, ensure data quality' : '审核AI自动识别的标签，确保数据质量' }}</p>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ pagination.total }}</span>
          <span class="stat-label">待审核</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ selectedImages.length }}</span>
          <span class="stat-label">已选择</span>
        </div>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-card">
      <div class="filter-content">
        <div class="filter-item">
          <label class="filter-label">{{ t('label.sceneType') }}</label>
          <div class="filter-input">
            <el-select v-model="filters.scene_type" :placeholder="t('user.login') === 'Login' ? 'All Scenes' : '全部场景'" clearable>
              <el-option v-for="s in enums.scene_types" :key="s" :label="s" :value="s" />
            </el-select>
          </div>
        </div>
        <div class="filter-item">
          <label class="filter-label">{{ t('label.weather') }}</label>
          <div class="filter-input">
            <el-select v-model="filters.weather" :placeholder="t('user.login') === 'Login' ? 'All Weather' : '全部天气'" clearable>
              <el-option v-for="w in enums.weather_types" :key="w" :label="w" :value="w" />
            </el-select>
          </div>
        </div>
        <div class="filter-actions">
          <button class="filter-btn primary" @click="loadData">
            <span class="btn-icon">⌕</span>
            <span class="btn-text">{{ t('common.search') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 待审核列表 -->
    <div class="list-card">
      <div class="list-header">
        <div class="list-title">
          <span class="title-dot"></span>
          <span>{{ t('user.login') === 'Login' ? 'Pending Review' : '待审核图片' }} ({{ pagination.total }})</span>
        </div>
        <div class="batch-actions">
          <button
            class="batch-btn success"
            :disabled="selectedImages.length === 0"
            @click="handleBatchCheck('checked')"
          >
            <span class="btn-icon">✓</span>
            <span class="btn-text">{{ t('user.login') === 'Login' ? 'Batch Approve' : '批量通过' }}</span>
            <span class="btn-badge">{{ selectedImages.length }}</span>
          </button>
          <button
            class="batch-btn danger"
            :disabled="selectedImages.length === 0"
            @click="handleBatchCheck('discard')"
          >
            <span class="btn-icon">✕</span>
            <span class="btn-text">{{ t('user.login') === 'Login' ? 'Batch Reject' : '批量废弃' }}</span>
            <span class="btn-badge">{{ selectedImages.length }}</span>
          </button>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="imageList"
        class="custom-table"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column label="缩略图" width="100">
          <template #default="{ row }">
            <div class="thumbnail-wrapper" v-if="row.stored_filename">
              <el-image
                :src="getImageUrl(row.file_path)"
                :preview-src-list="[getImageUrl(row.file_path)]"
                fit="cover"
                class="thumbnail"
              />
            </div>
            <div v-else class="thumbnail-placeholder">无图片</div>
          </template>
        </el-table-column>

        <el-table-column prop="original_filename" :label="t('image.filename')" min-width="200" show-overflow-tooltip />

        <el-table-column :label="t('user.login') === 'Login' ? 'Labels' : '标签信息'" min-width="300">
          <template #default="{ row }">
            <div class="label-tags" v-if="row.labels">
              <span v-if="row.labels.season" class="tag season">{{ row.labels.season }}</span>
              <span v-if="row.labels.weather" class="tag weather">{{ row.labels.weather }}</span>
              <span v-if="row.labels.scene_type" class="tag scene">{{ row.labels.scene_type }}</span>
              <span v-if="row.labels.light" class="tag light">{{ row.labels.light }}</span>
              <span v-if="row.labels.clarity" class="tag clarity" :class="row.labels.clarity === '清晰' ? 'good' : 'bad'">
                {{ row.labels.clarity }}
              </span>
            </div>
            <span v-else class="no-label">暂无标签</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" :label="t('image.createdAt')" width="180">
          <template #default="{ row }">
            <span class="time-text">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="t('image.actions')" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <button class="table-btn approve" @click="handleCheck(row.id, 'checked')">{{ t('user.login') === 'Login' ? 'Approve' : '通过' }}</button>
              <button class="table-btn reject" @click="handleCheck(row.id, 'discard')">{{ t('user.login') === 'Login' ? 'Reject' : '废弃' }}</button>
              <button class="table-btn view" @click="viewDetail(row.id)">{{ t('image.detail') }}</button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && imageList.length === 0" class="review-empty">
        <div class="empty-title">暂无待审核图片</div>
        <div class="empty-desc">可以先上传图片，或到图片管理查看已经完成审核的数据。</div>
        <div class="empty-actions">
          <button class="empty-btn primary" @click="router.push('/upload')">去上传</button>
          <button class="empty-btn" @click="router.push('/images')">查看图片管理</button>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <div class="pagination-info">
          共 <span class="total">{{ pagination.total }}</span> 条记录
        </div>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="sizes, prev, pager, next"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { imageApi, labelApi } from '@/api'
import dayjs from 'dayjs'
import { t } from '../utils/i18n'

const router = useRouter()
const loading = ref(false)
const imageList = ref<any[]>([])
const selectedImages = ref<any[]>([])
const enums = ref<any>({})

const filters = reactive({
  scene_type: '',
  weather: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

onMounted(() => {
  loadData()
  loadEnums()
})

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await imageApi.getList({
      page: pagination.page,
      page_size: pagination.pageSize,
      check_status: 'pending',
      ...filters,
    })
    imageList.value = res.items || []
    pagination.total = res.total || 0
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

const handleSelectionChange = (selection: any[]) => {
  selectedImages.value = selection
}

const handleCheck = async (imageId: number, status: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要${status === 'checked' ? '通过' : '废弃'}这张图片吗？`,
      '提示',
      { type: 'warning' }
    )
    await imageApi.check(imageId, status)
    ElMessage.success('操作成功')
    loadData()
  } catch (error) {
    // 取消操作
  }
}

const handleBatchCheck = async (status: string) => {
  const imageIds = selectedImages.value.map(img => img.id)
  try {
    await ElMessageBox.confirm(
      `确定要${status === 'checked' ? '通过' : '废弃'} ${imageIds.length} 张图片吗？`,
      '提示',
      { type: 'warning' }
    )
    await imageApi.batchCheck(imageIds, status)
    ElMessage.success('批量操作成功')
    loadData()
  } catch (error) {
    // 取消操作
  }
}

const viewDetail = (id: number) => {
  router.push(`/images/${id}`)
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const getImageUrl = (filePath: string) => {
  if (!filePath) return ''
  // 将反斜杠替换为正斜杠
  return '/' + filePath.replace(/\\/g, '/')
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.review-page {
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

/* 筛选 */
.filter-card {
  background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
}

.filter-content {
  display: flex;
  align-items: flex-end;
  gap: 20px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.filter-input {
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

.filter-actions {
  margin-left: auto;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;

  &.primary {
    background: #3b82f6;
    color: #fff;

    &:hover {
      background: #2563eb;
    }
  }
}

/* 待审核列表 */
.list-card {
  background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 24px;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.list-title {
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

.batch-actions {
  display: flex;
  gap: 12px;
}

.batch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.success {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;

    &:hover:not(:disabled) {
      background: rgba(16, 185, 129, 0.2);
    }
  }

  &.danger {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;

    &:hover:not(:disabled) {
      background: rgba(239, 68, 68, 0.2);
    }
  }
}

.btn-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

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

.review-empty {
  margin-top: 16px;
  padding: 32px;
  text-align: center;
  border: 1px dashed #334155;
  border-radius: 12px;
  background: #0f172a;
}

.empty-title {
  color: #f1f5f9;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-desc {
  color: #64748b;
  font-size: 13px;
  margin-bottom: 18px;
}

.empty-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.empty-btn {
  border: 1px solid #334155;
  background: #1e293b;
  color: #cbd5e1;
  border-radius: 8px;
  padding: 9px 14px;
  cursor: pointer;
  font-family: 'JetBrains Mono', monospace;

  &:hover {
    border-color: #3b82f6;
    color: #60a5fa;
  }

  &.primary {
    border-color: #3b82f6;
    background: rgba(59, 130, 246, 0.12);
    color: #60a5fa;
  }
}

.thumbnail-wrapper {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #1e293b;
}

.thumbnail {
  width: 100%;
  height: 100%;
}

.thumbnail-placeholder {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: #1e293b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #64748b;
}

.label-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;

  &.season {
    background: rgba(139, 92, 246, 0.1);
    color: #8b5cf6;
  }

  &.weather {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  &.scene {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }

  &.light {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  &.clarity {
    &.good {
      background: rgba(16, 185, 129, 0.1);
      color: #10b981;
    }

    &.bad {
      background: rgba(239, 68, 68, 0.1);
      color: #ef4444;
    }
  }
}

.no-label {
  font-size: 12px;
  color: #64748b;
}

.time-text {
  font-size: 13px;
  color: #94a3b8;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.table-btn {
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;

  &.approve {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;

    &:hover {
      background: rgba(16, 185, 129, 0.2);
    }
  }

  &.reject {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;

    &:hover {
      background: rgba(239, 68, 68, 0.2);
    }
  }

  &.view {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;

    &:hover {
      background: rgba(59, 130, 246, 0.2);
    }
  }
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #1e293b;
}

.pagination-info {
  font-size: 13px;
  color: #64748b;

  .total {
    color: #3b82f6;
    font-weight: 500;
  }
}

:deep(.el-pagination) {
  .el-pagination__total {
    color: #64748b;
  }

  .el-pagination__sizes {
    .el-input__wrapper {
      background: #0f172a;
      border: 1px solid #1e293b;
      box-shadow: none;
    }
  }

  .el-pager {
    li {
      background: #0f172a;
      color: #94a3b8;
      border: 1px solid #1e293b;

      &:hover {
        color: #3b82f6;
        border-color: #3b82f6;
      }

      &.is-active {
        background: #3b82f6;
        color: #fff;
        border-color: #3b82f6;
      }
    }
  }

  .btn-prev,
  .btn-next {
    background: #0f172a;
    color: #94a3b8;
    border: 1px solid #1e293b;

    &:hover {
      color: #3b82f6;
      border-color: #3b82f6;
    }
  }
}
</style>
