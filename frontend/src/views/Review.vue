<template>
  <div class="review-page">
    <!-- 筛选 -->
    <el-card shadow="hover" class="filter-card">
      <el-form :inline="true">
        <el-form-item label="场景">
          <el-select v-model="filters.scene_type" clearable placeholder="全部场景">
            <el-option v-for="s in enums.scene_types" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="天气">
          <el-select v-model="filters.weather" clearable placeholder="全部天气">
            <el-option v-for="w in enums.weather_types" :key="w" :label="w" :value="w" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 待审核列表 -->
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>待审核图片 ({{ pagination.total }})</span>
          <div>
            <el-button
              type="success"
              :disabled="selectedImages.length === 0"
              @click="handleBatchCheck('checked')"
            >
              批量通过 ({{ selectedImages.length }})
            </el-button>
            <el-button
              type="danger"
              :disabled="selectedImages.length === 0"
              @click="handleBatchCheck('discard')"
            >
              批量废弃 ({{ selectedImages.length }})
            </el-button>
          </div>
        </div>
      </template>

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

        <el-table-column label="标签信息" min-width="300">
          <template #default="{ row }">
            <div class="label-tags" v-if="row.labels">
              <el-tag v-if="row.labels.season" size="small">{{ row.labels.season }}</el-tag>
              <el-tag v-if="row.labels.weather" size="small" type="info">{{ row.labels.weather }}</el-tag>
              <el-tag v-if="row.labels.scene_type" size="small" type="warning">{{ row.labels.scene_type }}</el-tag>
              <el-tag v-if="row.labels.light" size="small" type="success">{{ row.labels.light }}</el-tag>
              <el-tag v-if="row.labels.clarity" size="small" :type="row.labels.clarity === '清晰' ? 'success' : 'danger'">
                {{ row.labels.clarity }}
              </el-tag>
            </div>
            <span v-else class="no-label">暂无标签</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="success" link @click="handleCheck(row.id, 'checked')">
              通过
            </el-button>
            <el-button type="danger" link @click="handleCheck(row.id, 'discard')">
              废弃
            </el-button>
            <el-button type="primary" link @click="viewDetail(row.id)">
              详情
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
import { imageApi, labelApi } from '@/api'
import dayjs from 'dayjs'

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
</script>

<style scoped lang="scss">
.review-page {
  .filter-card {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .thumbnail {
    width: 60px;
    height: 60px;
    border-radius: 4px;
  }

  .label-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .no-label {
    color: #909399;
    font-size: 12px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
