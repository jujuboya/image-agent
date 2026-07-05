<template>
  <div class="images-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="page-title">{{ t('nav.images') }}</h2>
        <p class="page-subtitle">{{ t('user.login') === 'Login' ? 'Manage and review uploaded images' : '管理和审核已上传的图片数据集' }}</p>
      </div>
      <div class="header-actions">
        <button class="action-btn primary" @click="loadData">
          <span class="btn-icon">↻</span>
          <span class="btn-text">{{ t('common.refresh') }}</span>
        </button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <div class="filter-card">
      <div class="filter-content">
        <div class="filter-item">
          <label class="filter-label">{{ t('user.login') === 'Login' ? 'Keyword' : '关键词' }}</label>
          <div class="filter-input">
            <el-input
              v-model="filters.keyword"
              :placeholder="t('user.login') === 'Login' ? 'Filename/UUID' : '文件名/UUID'"
              clearable
              @keyup.enter="loadData"
            />
          </div>
        </div>
        <div class="filter-item">
          <label class="filter-label">{{ t('image.status') }}</label>
          <div class="filter-input">
            <el-select v-model="filters.status" :placeholder="t('user.login') === 'Login' ? 'All Status' : '全部状态'" clearable>
              <el-option label="解析中" value="parsing" />
              <el-option label="已解析" value="parsed" />
              <el-option label="已通过" value="checked" />
              <el-option label="已废弃" value="discarded" />
            </el-select>
          </div>
        </div>
        <div class="filter-item">
          <label class="filter-label">{{ t('user.login') === 'Login' ? 'Review Status' : '审核状态' }}</label>
          <div class="filter-input">
            <el-select v-model="filters.check_status" :placeholder="t('user.login') === 'Login' ? 'All' : '全部'" clearable>
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="checked" />
              <el-option label="已废弃" value="discard" />
            </el-select>
          </div>
        </div>
        <div class="filter-actions">
          <button class="filter-btn primary" @click="loadData">
            <span class="btn-icon">⌕</span>
            <span class="btn-text">{{ t('common.search') }}</span>
          </button>
          <button class="filter-btn secondary" @click="resetFilters">
            <span class="btn-text">{{ t('common.reset') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 图片列表 -->
    <div class="list-card">
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
              >
                <template #error>
                  <div class="thumbnail-error">加载失败</div>
                </template>
              </el-image>
            </div>
            <div v-else class="thumbnail-placeholder">无图片</div>
          </template>
        </el-table-column>

        <el-table-column prop="original_filename" :label="t('image.filename')" min-width="200" show-overflow-tooltip />

        <el-table-column prop="file_size" :label="t('image.size')" width="100">
          <template #default="{ row }">
            <span class="size-text">{{ formatSize(row.file_size) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="width" :label="t('image.dimensions')" width="120">
          <template #default="{ row }">
            <span class="dimension-text">{{ row.width }} × {{ row.height }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" :label="t('image.status')" width="100">
          <template #default="{ row }">
            <span class="status-tag" :class="row.status">
              {{ getStatusLabel(row.status) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="check_status" :label="t('user.login') === 'Login' ? 'Review' : '审核'" width="100">
          <template #default="{ row }">
            <span class="check-tag" :class="row.check_status">
              {{ getCheckStatusLabel(row.check_status) }}
            </span>
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
              <button class="table-btn view" @click="viewDetail(row.id)">{{ t('image.detail') }}</button>
              <button class="table-btn delete" @click="handleDelete(row.id)">{{ t('image.delete') }}</button>
            </div>
          </template>
        </el-table-column>
      </el-table>

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
import { imageApi } from '@/api'
import dayjs from 'dayjs'
import { t } from '../utils/i18n'

const router = useRouter()
const loading = ref(false)
const imageList = ref<any[]>([])
const selectedImages = ref<any[]>([])

const filters = reactive({
  keyword: '',
  status: '',
  check_status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

onMounted(() => {
  loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    const res: any = await imageApi.getList({
      page: pagination.page,
      page_size: pagination.pageSize,
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

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.check_status = ''
  pagination.page = 1
  loadData()
}

const handleSelectionChange = (selection: any[]) => {
  selectedImages.value = selection
}

const viewDetail = (id: number) => {
  router.push(`/images/${id}`)
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这张图片吗？', '提示', {
      type: 'warning',
    })
    await imageApi.delete(id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    // 取消操作
  }
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    uploading: '上传中',
    parsing: '解析中',
    parsed: '已解析',
    labeling: '标注中',
    labeled: '已标注',
    checking: '审核中',
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

const getCheckStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    checked: '已通过',
    discard: '已废弃',
  }
  return map[status] || status
}
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.images-page {
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

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
    }
  }
}

/* 搜索筛选 */
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
  flex-wrap: wrap;
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

  :deep(.el-select) {
    .el-input__wrapper {
      background: #0f172a;
      border: 1px solid #1e293b;
      box-shadow: none;
    }
  }
}

.filter-actions {
  display: flex;
  gap: 12px;
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

  &.secondary {
    background: #1e293b;
    color: #94a3b8;

    &:hover {
      background: #334155;
      color: #f1f5f9;
    }
  }
}

/* 图片列表 */
.list-card {
  background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 24px;
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

  :deep(.el-table__empty-block) {
    background: transparent;
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

.thumbnail-error {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: #1e293b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #ef4444;
}

.size-text,
.dimension-text,
.time-text {
  font-size: 13px;
  color: #94a3b8;
}

.status-tag,
.check-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;

  &.parsing,
  &.pending {
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

  &.discarded,
  &.discard {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.table-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'JetBrains Mono', monospace;

  &.view {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;

    &:hover {
      background: rgba(59, 130, 246, 0.2);
    }
  }

  &.delete {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;

    &:hover {
      background: rgba(239, 68, 68, 0.2);
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
