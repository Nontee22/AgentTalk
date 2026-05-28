<script setup lang="ts">
import type { CharacterSummary } from '@/types/world'
import TagBadge from '@/components/common/TagBadge.vue'
import { MessageCircle } from 'lucide-vue-next'

defineProps<{
  character: CharacterSummary
}>()

defineEmits<{
  click: []
}>()
</script>

<template>
  <div
    class="rounded-card border border-white/[0.08] bg-bg-surface overflow-hidden hover:border-accent/40 transition-all duration-300 cursor-pointer"
    @click="$emit('click')"
  >
    <div class="p-5 flex flex-col items-center text-center">
      <div class="w-20 h-20 rounded-full overflow-hidden bg-bg-hover mb-3 border-2 border-white/[0.08]">
        <img
          v-if="character.avatar"
          :src="`/api/static/${character.avatar}`"
          :alt="character.name"
          class="w-full h-full object-cover"
        />
        <div v-else class="w-full h-full flex items-center justify-center">
          <span class="text-2xl font-serif text-accent/40">{{ character.name[0] }}</span>
        </div>
      </div>

      <h3 class="font-serif text-text-primary font-semibold mb-1">
        {{ character.name }}
      </h3>
      <p v-if="character.identity" class="text-text-secondary text-xs mb-3 line-clamp-2">
        {{ character.identity }}
      </p>

      <div class="flex flex-wrap justify-center gap-1 mb-4" v-if="character.tags?.length">
        <TagBadge v-for="tag in character.tags" :key="tag" :label="tag" />
      </div>

      <button
        class="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-accent/10 text-accent text-sm hover:bg-accent/20 transition-colors"
        disabled
        title="对话功能开发中"
      >
        <MessageCircle :size="14" />
        开始对话
      </button>
    </div>
  </div>
</template>
