import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, TokenResponse } from '@/types'

const TOKEN_KEY = 'ci_access_token'
const REFRESH_KEY = 'ci_refresh_token'
const USER_KEY = 'ci_user'

export const useAuthStore = defineStore('auth', () => {
  // ---------- 状态 ----------
  const accessToken = ref(localStorage.getItem(TOKEN_KEY) || '')
  const refreshToken = ref(localStorage.getItem(REFRESH_KEY) || '')
  const user = ref<User | null>(loadUser())

  // ---------- 计算属性 ----------
  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)
  const userRole = computed(() => user.value?.role || 'viewer')
  const displayName = computed(() => user.value?.display_name || user.value?.username || '')

  // ---------- 辅助 ----------
  function loadUser(): User | null {
    try {
      const raw = localStorage.getItem(USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }

  function saveTokens(tokenResp: TokenResponse) {
    accessToken.value = tokenResp.access_token
    refreshToken.value = tokenResp.refresh_token
    localStorage.setItem(TOKEN_KEY, tokenResp.access_token)
    localStorage.setItem(REFRESH_KEY, tokenResp.refresh_token)
  }

  function saveUser(u: User) {
    user.value = u
    localStorage.setItem(USER_KEY, JSON.stringify(u))
  }

  // ---------- Actions ----------
  async function login(username: string, password: string) {
    const { data } = await authApi.login({ username, password })
    saveTokens(data)
    // 获取用户信息
    const { data: me } = await authApi.getMe()
    saveUser(me)
  }

  async function register(payload: { username: string; email: string; password: string; display_name?: string }) {
    await authApi.register(payload)
  }

  async function fetchUser() {
    try {
      const { data } = await authApi.getMe()
      saveUser(data)
    } catch {
      logout()
    }
  }

  async function refreshAccessToken(): Promise<string> {
    const { data } = await authApi.refreshToken(refreshToken.value)
    saveTokens(data)
    return data.access_token
  }

  function logout() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
  }

  // 初始化：有 token 但无用户信息时自动拉取
  async function init() {
    if (accessToken.value && !user.value) {
      await fetchUser()
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    isLoggedIn,
    userRole,
    displayName,
    login,
    register,
    fetchUser,
    refreshAccessToken,
    logout,
    init,
  }
})
