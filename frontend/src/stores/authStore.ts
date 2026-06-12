import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { login as apiLogin, register as apiRegister, getProfile } from '@/api/auth'
import { useToast } from '@/composables/useToast'
import type { LoginRequest, RegisterRequest, User } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const { showToast } = useToast()

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  function setTokens(accessToken: string, refreshToken: string) {
    token.value = accessToken
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }

  function clearTokens() {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function login(data: LoginRequest) {
    const res = await apiLogin(data)
    setTokens(res.access_token, res.refresh_token)
    await fetchProfile()
  }

  async function register(data: RegisterRequest) {
    const res = await apiRegister(data)
    setTokens(res.access_token, res.refresh_token)
    await fetchProfile()
  }

  function logout() {
    clearTokens()
    showToast('已退出登录', 'success')
  }

  async function fetchProfile() {
    try {
      user.value = await getProfile()
    } catch {
      clearTokens()
    }
  }

  async function initAuth() {
    if (token.value) {
      await fetchProfile()
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    initAuth,
    setTokens,
    clearTokens,
    fetchProfile,
  }
})
