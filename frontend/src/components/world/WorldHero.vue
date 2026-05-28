<script setup lang="ts">
import type { WorldBook } from '@/types/world'
import TagBadge from '@/components/common/TagBadge.vue'

defineProps<{
  world: WorldBook
}>()
</script>

<template>
  <div class="relative h-72 md:h-96 overflow-hidden bg-bg-deep">
    <img
      v-if="world.cover_image"
      :src="`/api/static/${world.cover_image}`"
      :alt="world.name"
      class="w-full h-full object-cover"
    />
    <div
      v-else
      class="w-full h-full flex items-center justify-center"
    >
      <span class="text-8xl font-serif text-accent/20">{{ world.name[0] }}</span>
    </div>

    <div class="absolute inset-0 bg-gradient-to-t from-bg-base via-bg-base/40 to-transparent" />

    <div class="absolute bottom-0 left-0 right-0 p-8">
      <h1 class="font-serif text-3xl md:text-4xl text-text-primary font-bold mb-2 tracking-wide">
        {{ world.name }}
      </h1>
      <div class="flex gap-2" v-if="world.tags?.length">
        <TagBadge v-for="tag in world.tags" :key="tag" :label="tag" variant="accent" />
      </div>
    </div>
  </div>
</template>
