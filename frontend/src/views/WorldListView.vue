<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWorldStore } from '@/stores/worldStore'
import WorldCard from '@/components/world/WorldCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const store = useWorldStore()

const selectedTag = ref<string | null>(null)
const searchQuery = ref((route.query.search as string) || '')

const commonTags = ['奇幻', '科幻', '历史', '现实']

function selectTag(tag: string | null) {
  selectedTag.value = tag
  loadWorlds()
}

function loadWorlds() {
  store.fetchWorlds({
    tag: selectedTag.value || undefined,
    search: searchQuery.value || undefined,
  })
}

watch(
  () => route.query.search,
  (val) => {
    searchQuery.value = (val as string) || ''
    loadWorlds()
  },
)

onMounted(loadWorlds)
</script>

<template>
  <main class="max-w-7xl mx-auto px-6 py-8">
    <div class="mb-8">
      <h1 class="font-serif text-2xl text-text-primary mb-2">探索世界</h1>
      <p class="text-text-secondary text-sm">探索不同的世界，与其中的角色展开对话</p>
    </div>

    <div class="flex gap-2 mb-8">
      <button
        class="px-3 py-1.5 rounded-full text-sm transition-colors"
        :class="
          selectedTag === null
            ? 'bg-accent text-bg-deep'
            : 'bg-white/[0.06] text-text-secondary hover:bg-white/[0.1]'
        "
        @click="selectTag(null)"
      >
        全部
      </button>
      <button
        v-for="tag in commonTags"
        :key="tag"
        class="px-3 py-1.5 rounded-full text-sm transition-colors"
        :class="
          selectedTag === tag
            ? 'bg-accent text-bg-deep'
            : 'bg-white/[0.06] text-text-secondary hover:bg-white/[0.1]'
        "
        @click="selectTag(tag)"
      >
        {{ tag }}
      </button>
    </div>

    <div v-if="store.loading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      <div
        v-for="n in 8"
        :key="n"
        class="rounded-card bg-bg-surface border border-white/[0.08] overflow-hidden animate-pulse"
      >
        <div class="aspect-[3/4] bg-bg-hover" />
        <div class="p-4 space-y-2">
          <div class="h-4 bg-bg-hover rounded w-2/3" />
          <div class="h-3 bg-bg-hover rounded w-full" />
          <div class="h-3 bg-bg-hover rounded w-1/2" />
        </div>
      </div>
    </div>

    <div
      v-else-if="store.worlds.length"
      class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"
    >
      <WorldCard v-for="world in store.worlds" :key="world.id" :world="world" />
    </div>

    <EmptyState
      v-else
      message="还没有世界书，创建你的第一个世界"
      action-label="创建世界"
      @action="router.push({ name: 'world-create' })"
    />
  </main>
</template>
