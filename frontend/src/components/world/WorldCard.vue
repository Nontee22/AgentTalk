<script setup lang="ts">
import type { WorldBookSummary } from '@/types/world'
import TagBadge from '@/components/common/TagBadge.vue'
import { Users } from 'lucide-vue-next'

defineProps<{
  world: WorldBookSummary
}>()
</script>

<template>
  <router-link
    :to="{ name: 'world-detail', params: { id: world.id } }"
    class="group block rounded-card border border-white/[0.08] bg-bg-surface overflow-hidden hover:border-accent/60 hover:-translate-y-0.5 transition-all duration-300"
  >
    <div class="aspect-[3/4] overflow-hidden bg-bg-deep">
      <img
        v-if="world.cover_image"
        :src="`/api/static/${world.cover_image}`"
        :alt="world.name"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
      />
      <div
        v-else
        class="w-full h-full flex items-center justify-center text-text-muted"
      >
        <span class="text-4xl font-serif text-accent/30">{{ world.name[0] }}</span>
      </div>
    </div>

    <div class="p-4">
      <h3 class="font-serif text-text-primary font-semibold truncate mb-1">
        {{ world.name }}
      </h3>
      <p
        v-if="world.description"
        class="text-text-secondary text-xs leading-relaxed line-clamp-2 mb-3"
      >
        {{ world.description }}
      </p>

      <div class="flex flex-wrap gap-1.5 mb-3" v-if="world.tags?.length">
        <TagBadge v-for="tag in world.tags" :key="tag" :label="tag" />
      </div>

      <div class="flex items-center gap-1 text-text-muted text-xs">
        <Users :size="12" />
        <span>{{ world.character_count }} 个角色</span>
      </div>
    </div>
  </router-link>
</template>
