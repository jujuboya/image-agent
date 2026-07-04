<template>
  <div class="images-page">
    <!-- 搜索筛选 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="文件名/UUID"
            clearable
            @keyup.enter="loadData"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态">
            <el-option label="解析中" value="parsing" />
            <el-option label="已解析" value="parsed" />
            <el-option label="已通过" value="checked" />
            <el-option label="已废弃" value="discarded" />
          </el-select>
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="filters.check_status" clearable placeholder="全部">
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="checked" />
            <el-option label="已废弃" value="discard" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 图片列表 -->
    <el-card shadow="hover">
      <el-table
        v-loading="loading"
        :data="imageList"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column label="缩略图" width="100">
          <template #default="{ row }">
            <el-image
              :src="`/uploads/temp/${row.stored_filename}`"
              :preview-src-list="[`/uploads/temp/${row.stored_filename}`]"
              fit="cover"
              class="thumbnail"
            />
          </template>
        </el-table-column>

        <el-table-column prop="original_filename" label="文件名" min-width="200" show-overflow-tooltip />

        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>

        <el-table-column prop="width" label="尺寸" width="120">
          <template #default="{ row }">
            {{ row.width }} × {{ row.height }}
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="check_status" label="审核" width="100">
          <template #default="{ row }">
            <el-tag :type="getCheckStatusType(row.check_status)">
              {{ getCheckStatusLabel(row.check_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row.id)">
              详情
            </el-button>
            <el-button type="danger" link @click="handleDelete(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { imageApi } from '@/api'
import dayjs from 'dayjs'

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
    labeling: '标注中',
    labeled: '已标注',
    checking: '审核中',
    checked: '已通过',
    discarded: '已废弃',
  }
  return map[status] || status
}

const getCheckStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    checked: 'success',
    discard: 'danger',
  }
  return map[status] || 'info'
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
.images-page {
  .filter-card {
    margin-bottom: 20px;
  }

  .thumbnail {
    width: 60px;
    height: 60px;
    border-radius: 4px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
