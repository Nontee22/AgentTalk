<script setup lang="ts">
import type { Character } from '@/types/world'
import { X, MessageCircle } from 'lucide-vue-next'
import FoldableSection from '@/components/common/FoldableSection.vue'
import TagBadge from '@/components/common/TagBadge.vue'

defineProps<{
  character: Character
  open: boolean
}>()

defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="fixed inset-0 z-50 flex justify-end">
        <div class="absolute inset-0 bg-black/50" @click="$emit('close')" />

        <div class="relative w-[400px] max-w-full bg-bg-surface border-l border-white/[0.08] overflow-y-auto flex flex-col">
          <div class="sticky top-0 z-10 flex items-center justify-end p-4 bg-bg-surface/80 backdrop-blur-sm">
            <button
              class="p-1.5 rounded-lg hover:bg-white/[0.06] text-text-muted hover:text-text-primary transition-colors"
              @click="$emit('close')"
            >
              <X :size="18" />
            </button>
          </div>

          <div class="flex-1 px-6 pb-6">
            <div class="flex flex-col items-center text-center mb-6">
              <div class="w-24 h-24 rounded-full overflow-hidden bg-bg-hover mb-4 border-2 border-white/[0.08]">
                <img
                  v-if="character.avatar"
                  :src="`/api/static/${character.avatar}`"
                  :alt="character.name"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="text-3xl font-serif text-accent/40">{{ character.name[0] }}</span>
                </div>
              </div>
              <h2 class="font-serif text-xl text-text-primary font-semibold mb-1">
                {{ character.name }}
              </h2>
              <p v-if="character.identity" class="text-text-secondary text-sm">
                {{ character.identity }}
              </p>
              <div class="flex flex-wrap justify-center gap-1.5 mt-3" v-if="character.tags?.length">
                <TagBadge v-for="tag in character.tags" :key="tag" :label="tag" />
              </div>
            </div>

            <div class="space-y-0">
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

              <FoldableSection v-if="character.knowledge" title="知识范围">
                {{ character.knowledge }}
              </FoldableSection>

              <FoldableSection v-if="character.greeting" title="开场白">
                {{ character.greeting }}
              </FoldableSection>
            </div>
          </div>

          <div class="sticky bottom-0 p-4 border-t border-white/[0.06] bg-bg-surface">
            <button
              class="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-accent text-bg-deep font-medium opacity-50 cursor-not-allowed"
              disabled
              title="对话功能开发中"
            >
              <MessageCircle :size="16" />
              开始对话
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.3s ease;
}
.drawer-enter-active > :last-child,
.drawer-leave-active > :last-child {
  transition: transform 0.3s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from > :last-child,
.drawer-leave-to > :last-child {
  transform: translateX(100%);
}
</style>
