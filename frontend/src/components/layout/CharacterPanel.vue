<script setup lang="ts">
import { PanelRightClose } from 'lucide-vue-next'
import type { Character } from '@/types/world'
import type { WorldBook } from '@/types/world'
import FoldableSection from '@/components/common/FoldableSection.vue'

defineProps<{
  character: Character | null
  world: WorldBook | null
}>()

defineEmits<{
  close: []
}>()
</script>

<template>
  <aside
    v-if="character"
    class="w-[300px] border-l border-white/[0.06] bg-bg-deep flex flex-col h-full overflow-y-auto"
  >
    <div class="flex items-center justify-between p-3 border-b border-white/[0.06]">
      <span class="text-xs text-text-muted">角色信息</span>
      <button
        class="p-1 rounded hover:bg-white/[0.06] text-text-muted hover:text-text-primary transition-colors"
        @click="$emit('close')"
      >
        <PanelRightClose :size="14" />
      </button>
    </div>

    <div class="p-4">
      <div class="flex flex-col items-center text-center mb-5">
        <div class="w-16 h-16 rounded-full overflow-hidden bg-bg-hover mb-3 border-2 border-white/[0.08]">
          <img
            v-if="character.avatar"
            :src="`/api/static/${character.avatar}`"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-xl font-serif text-accent/40">
            {{ character.name[0] }}
          </div>
        </div>
        <h3 class="font-serif text-text-primary font-semibold text-sm">{{ character.name }}</h3>
        <p v-if="character.identity" class="text-text-secondary text-xs mt-0.5">{{ character.identity }}</p>
      </div>

      <div class="space-y-0 text-xs">
        <FoldableSection v-if="character.personality" title="性格">
          {{ character.personality }}
        </FoldableSection>
        <FoldableSection v-if="character.background" title="经历">
          {{ character.background }}
        </FoldableSection>
        <FoldableSection v-if="character.relationships" title="关系">
          {{ character.relationships }}
        </FoldableSection>
        <FoldableSection v-if="character.language_style" title="说话风格">
          {{ character.language_style }}
        </FoldableSection>
        <FoldableSection v-if="character.knowledge" title="已知信息">
          {{ character.knowledge }}
        </FoldableSection>
      </div>

      <div v-if="world" class="mt-6 pt-4 border-t border-white/[0.06]">
        <p class="text-[10px] text-text-muted mb-1">世界背景</p>
        <p class="text-xs text-text-secondary font-serif">{{ world.name }}</p>
        <p v-if="world.description" class="text-[10px] text-text-muted mt-1 line-clamp-3">
          {{ world.description }}
        </p>
        <router-link
          :to="{ name: 'world-detail', params: { id: world.id } }"
          class="text-[10px] text-accent hover:text-accent-hover mt-2 inline-block"
        >
          查看完整世界观
        </router-link>
      </div>
    </div>
  </aside>
</template>
