<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { showToast } = useToast()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  if (!username.value || !password.value) {
    errorMsg.value = '请填写用户名和密码'
    return
  }

  loading.value = true
  try {
    await auth.login({ username: username.value, password: password.value })
    showToast('登录成功', 'success')
    const redirect = (route.query.redirect as string) || '/worlds'
    router.push(redirect)
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-bg-base flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <span class="text-accent text-3xl">&#10022;</span>
        <h1 class="font-serif text-text-primary text-2xl font-semibold mt-2">角色世界</h1>
        <p class="text-text-secondary text-sm mt-1">登录以开始你的冒险</p>
      </div>

      <form
        class="bg-bg-surface rounded-xl border border-white/[0.08] p-6 space-y-4"
        @submit.prevent="handleLogin"
      >
        <div>
          <label class="block text-text-secondary text-sm mb-1.5">用户名 / 邮箱</label>
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
            placeholder="请输入用户名或邮箱"
          />
        </div>

        <div>
          <label class="block text-text-secondary text-sm mb-1.5">密码</label>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
            placeholder="请输入密码"
          />
        </div>

        <div v-if="errorMsg" class="text-danger text-sm">{{ errorMsg }}</div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2 rounded-lg bg-accent text-bg-deep text-sm font-medium hover:bg-accent-hover transition-colors disabled:opacity-50"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <p class="text-center text-text-secondary text-sm">
          还没有账号？
          <router-link to="/register" class="text-accent hover:text-accent-hover transition-colors">
            立即注册
          </router-link>
        </p>
      </form>
    </div>
  </div>
</template>
