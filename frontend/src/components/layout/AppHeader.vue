<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Plus } from 'lucide-vue-next'

const router = useRouter()
const searchQuery = ref('')

function handleSearch() {
  const q = searchQuery.value.trim()
  router.push({ name: 'worlds', query: q ? { search: q } : {} })
}
</script>

<template>
  <header class="sticky top-0 z-40 bg-bg-deep/80 backdrop-blur-md border-b border-white/[0.06]">
    <div class="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between gap-4">
      <router-link to="/worlds" class="flex items-center gap-2 shrink-0">
        <span class="text-accent text-lg">&#10022;</span>
        <span class="font-serif text-text-primary text-lg font-semibold">角色世界</span>
      </router-link>

      <div class="flex-1 max-w-md">
        <form class="relative" @submit.prevent="handleSearch">
          <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索世界书..."
            class="w-full rounded-lg bg-bg-surface border border-white/[0.08] pl-9 pr-3 py-1.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors"
          />
        </form>
      </div>

      <router-link
        to="/worlds/create"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent text-bg-deep text-sm font-medium hover:bg-accent-hover transition-colors shrink-0"
      >
        <Plus :size="16" />
        创建世界
      </router-link>
    </div>
  </header>
</template>
