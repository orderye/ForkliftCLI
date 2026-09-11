import axios from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'forklift_admin_token'

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// 请求拦截：统一注入 JWT
request.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一返回 data；401 跳登录；错误统一提示
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.message || error.message || '请求失败'

    if (status === 401) {
      clearToken()
      // 避免在登录页重复跳转
      if (!window.location.pathname.endsWith('/login')) {
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
      }
    } else if (status === 403) {
      ElMessage.error(msg || '无权限访问')
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  },
)

export default request
