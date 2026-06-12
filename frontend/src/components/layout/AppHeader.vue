<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Plus, LogOut, User, ChevronDown } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const auth = useAuthStore()
const searchQuery = ref('')
const showDropdown = ref(false)

const displayName = computed(
  () => auth.user?.nickname || auth.user?.username || '用户',
)

function handleSearch() {
  const q = searchQuery.value.trim()
  router.push({ name: 'worlds', query: q ? { search: q } : {} })
}

function handleLogout() {
  showDropdown.value = false
  auth.logout()
  router.push('/login')
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

      <div class="flex items-center gap-3 shrink-0">
        <router-link
          to="/worlds/create"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent text-bg-deep text-sm font-medium hover:bg-accent-hover transition-colors"
        >
          <Plus :size="16" />
          创建世界
        </router-link>

        <div class="relative">
          <button
            class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-bg-hover transition-colors"
            @click="showDropdown = !showDropdown"
            @blur="setTimeout(() => (showDropdown = false), 150)"
          >
            <div class="w-7 h-7 rounded-full bg-accent/20 flex items-center justify-center">
              <User :size="14" class="text-accent" />
            </div>
            <span class="text-text-primary text-sm max-w-[80px] truncate">{{ displayName }}</span>
            <ChevronDown :size="14" class="text-text-muted" />
          </button>

          <div
            v-if="showDropdown"
            class="absolute right-0 top-full mt-1 w-40 bg-bg-surface border border-white/[0.08] rounded-lg shadow-lg py-1 z-50"
          >
            <button
              class="w-full px-3 py-2 text-left text-sm text-text-primary hover:bg-bg-hover transition-colors flex items-center gap-2"
              @mousedown="handleLogout"
            >
              <LogOut :size="14" class="text-text-secondary" />
              退出登录
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
