<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-[80vh] text-center">
    <h1 class="font-serif text-6xl text-text-muted mb-4">404</h1>
    <p class="text-text-secondary text-sm mb-6">页面不存在</p>
    <button
      class="px-4 py-2 rounded-lg bg-accent text-bg-deep text-sm hover:bg-accent-hover transition-colors"
      @click="router.push({ name: 'worlds' })"
    >
      返回首页
    </button>
  </div>
</template>
