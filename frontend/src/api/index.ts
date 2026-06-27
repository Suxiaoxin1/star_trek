import axios from 'axios'
import router from '@/router'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：自动携带 JWT Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ci_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理 401 自动刷新 Token
let isRefreshing = false
let pendingRequests: Array<(token: string) => void> = []

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshTokenValue = localStorage.getItem('ci_refresh_token')

      // 如果没有 refresh_token，直接登出
      if (!refreshTokenValue) {
        clearAuth()
        router.push('/login')
        return Promise.reject(error)
      }

      // 防止并发刷新
      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const { data } = await api.post('/auth/refresh', { refresh_token: refreshTokenValue })
        localStorage.setItem('ci_access_token', data.access_token)
        localStorage.setItem('ci_refresh_token', data.refresh_token)

        // 重试所有等待的请求
        pendingRequests.forEach((cb) => cb(data.access_token))
        pendingRequests = []

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return api(originalRequest)
      } catch {
        clearAuth()
        router.push('/login')
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    // 处理 422 Pydantic 验证错误
    if (error.response?.status === 422) {
      const detail = error.response?.data?.detail
      // Pydantic v2 返回数组格式的验证错误
      if (Array.isArray(detail)) {
        const msgs = detail.map((e: any) => {
          const loc = e.loc?.join('.') || ''
          return `${loc}: ${e.msg}`
        })
        console.error('[API 422 Validation Error]', msgs)
        const fullMsg = msgs.join('; ')
        ElMessage.error({ message: `数据验证失败: ${fullMsg}`, duration: 8000 })
        return Promise.reject(error)
      }
    }

    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error('[API Error]', msg)
    return Promise.reject(error)
  },
)

function clearAuth() {
  localStorage.removeItem('ci_access_token')
  localStorage.removeItem('ci_refresh_token')
  localStorage.removeItem('ci_user')
}

export default api
