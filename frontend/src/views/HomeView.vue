<script setup lang="ts">
import { onMounted, ref } from 'vue'

import api from '@/api'

const healthStatus = ref('checking...')
const dbStatus = ref('')
const redisStatus = ref('')

onMounted(async () => {
  try {
    const response = await api.get('/health')
    healthStatus.value = response.data.status
    dbStatus.value = response.data.database
    redisStatus.value = response.data.redis
  } catch {
    healthStatus.value = 'unreachable'
  }
})
</script>

<template>
  <div class="min-h-screen bg-bg-base flex items-center justify-center">
    <div class="text-center">
      <h1 class="text-4xl font-serif text-accent mb-2">
        &#10022; 角色世界
      </h1>
      <p class="text-text-secondary mb-8">角色扮演对话系统</p>
      <div class="bg-bg-surface rounded-card p-6 border border-white/[0.08] inline-block text-left">
        <h2 class="text-text-primary text-sm font-semibold mb-3">系统状态</h2>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between gap-8">
            <span class="text-text-secondary">API</span>
            <span :class="healthStatus === 'healthy' ? 'text-green-400' : 'text-red-400'">
              {{ healthStatus }}
            </span>
          </div>
          <div class="flex justify-between gap-8">
            <span class="text-text-secondary">Database</span>
            <span :class="dbStatus === 'connected' ? 'text-green-400' : 'text-red-400'">
              {{ dbStatus || '—' }}
            </span>
          </div>
          <div class="flex justify-between gap-8">
            <span class="text-text-secondary">Redis</span>
            <span :class="redisStatus === 'connected' ? 'text-green-400' : 'text-red-400'">
              {{ redisStatus || '—' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
