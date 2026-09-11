import { defineStore } from 'pinia'
import { login as loginApi } from '@/api/auth'
import { dashboardApi } from '@/api/admin'
import { clearToken, getToken, setToken } from '@/api/request'
import type { LoginUser } from '@/api/types'

const USER_KEY = 'forklift_admin_user'

interface AuthState {
  token: string
  user: LoginUser | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: getToken(),
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    // 后端审计日志仅 role=admin（超级管理员）可访问
    isSuperAdmin: (state) => state.user?.role === 'admin',
  },

  actions: {
    /**
     * 登录后立即请求看板接口校验后台权限：
     * 普通用户即使有 token 也无法进入后台（后端 403）。
     */
    async login(phone: string, password: string) {
      const res = await loginApi(phone, password)
      setToken(res.access_token)
      this.token = res.access_token
      this.user = res.user
      localStorage.setItem(USER_KEY, JSON.stringify(res.user))

      try {
        await dashboardApi.stats()
      } catch (e: any) {
        // 403 = 非管理账号，回滚登录态
        this.logout()
        throw new Error('该账号无后台管理权限')
      }
    },

    logout() {
      clearToken()
      localStorage.removeItem(USER_KEY)
      this.token = ''
      this.user = null
    },
  },
})
