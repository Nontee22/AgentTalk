<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const auth = useAuthStore()
const { showToast } = useToast()

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function handleRegister() {
  errorMsg.value = ''

  if (!username.value || !email.value || !password.value) {
    errorMsg.value = '请填写所有字段'
    return
  }
  if (password.value.length < 6) {
    errorMsg.value = '密码长度至少 6 位'
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    await auth.register({
      username: username.value,
      email: email.value,
      password: password.value,
    })
    showToast('注册成功', 'success')
    router.push('/worlds')
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || '注册失败，请稍后重试'
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
        <p class="text-text-secondary text-sm mt-1">创建账号，探索不同的世界</p>
      </div>

      <form
        class="bg-bg-surface rounded-xl border border-white/[0.08] p-6 space-y-4"
        @submit.prevent="handleRegister"
      >
        <div>
          <label class="block text-text-secondary text-sm mb-1.5">用户名</label>
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
            placeholder="2-50 个字符"
          />
        </div>

        <div>
          <label class="block text-text-secondary text-sm mb-1.5">邮箱</label>
          <input
            v-model="email"
            type="email"
            autocomplete="email"
            class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
            placeholder="your@email.com"
          />
        </div>

        <div>
          <label class="block text-text-secondary text-sm mb-1.5">密码</label>
          <input
            v-model="password"
            type="password"
            autocomplete="new-password"
            class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
            placeholder="至少 6 位"
          />
        </div>

        <div>
          <label class="block text-text-secondary text-sm mb-1.5">确认密码</label>
          <input
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            class="w-full rounded-lg bg-bg-deep border border-white/[0.08] px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
            placeholder="再次输入密码"
          />
        </div>

        <div v-if="errorMsg" class="text-danger text-sm">{{ errorMsg }}</div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2 rounded-lg bg-accent text-bg-deep text-sm font-medium hover:bg-accent-hover transition-colors disabled:opacity-50"
        >
          {{ loading ? '注册中...' : '注册' }}
        </button>

        <p class="text-center text-text-secondary text-sm">
          已有账号？
          <router-link to="/login" class="text-accent hover:text-accent-hover transition-colors">
            立即登录
          </router-link>
        </p>
      </form>
    </div>
  </div>
</template>
