import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          ElMessage.error(data.detail || '用户名或密码错误')
          if (window.location.pathname !== '/login') {
            localStorage.removeItem('token')
            window.location.href = '/login'
          }
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          ElMessage.error(data.detail || '请求参数错误')
          break
        default:
          ElMessage.error(data.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

export default api

// ==================== 认证API ====================
export const authApi = {
  login: (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  register: (data: { username: string; password: string; nickname?: string }) => {
    return api.post('/auth/register', data)
  },

  getMe: () => api.get('/auth/me'),
}

// ==================== 上传API ====================
export const uploadApi = {
  uploadImage: (file: File, onProgress?: (percent: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)

    return api.post('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      },
    })
  },

  uploadBatch: (files: File[]) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))

    return api.post('/upload/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// ==================== 图片API ====================
export const imageApi = {
  getList: (params: {
    page?: number
    page_size?: number
    status?: string
    check_status?: string
    scene_type?: string
    weather?: string
    season?: string
    keyword?: string
  }) => api.get('/image/list', { params }),

  getDetail: (id: number) => api.get(`/image/${id}`),

  check: (imageId: number, status: string, comment?: string) => {
    return api.post('/image/check', { image_id: imageId, status, comment })
  },

  batchCheck: (imageIds: number[], status: string) => {
    return api.post('/image/batch-check', { image_ids: imageIds, status })
  },

  delete: (id: number) => api.delete(`/image/${id}`),

  getStats: () => api.get('/image/stats/overview'),
}

// ==================== 标签API ====================
export const labelApi = {
  getEnums: () => api.get('/label/enums'),

  getLabel: (imageId: number) => api.get(`/label/${imageId}`),

  update: (data: {
    image_id: number
    season?: string
    time_period?: string
    day_type?: string
    weather?: string
    temperature?: number
    humidity?: number
    light?: string
    shoot_angle?: string
    scene_scale?: string
    clarity?: string
    exposure?: string
    scene_type?: string
    device_type?: string
    province?: string
    city?: string
    district?: string
    address?: string
  }) => api.put('/label/update', data),

  batchUpdate: (imageIds: number[], labels: any) => {
    return api.post('/label/batch-update', { image_ids: imageIds, labels })
  },
}

// ==================== 数据集API ====================
export const datasetApi = {
  getVersions: () => api.get('/dataset/versions'),

  export: (data: {
    format: string
    filters?: any
    version_name?: string
  }) => api.post('/dataset/export', data, { responseType: 'blob' }),

  getStats: () => api.get('/dataset/stats'),
}
