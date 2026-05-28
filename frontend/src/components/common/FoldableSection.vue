<script setup lang="ts">
import { ref } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

defineProps<{
  title: string
  defaultOpen?: boolean
}>()

const isOpen = ref(false)
</script>

<template>
  <div class="border-b border-white/[0.06]">
    <button
      class="flex w-full items-center justify-between py-3 text-left text-sm font-medium text-text-primary hover:text-accent transition-colors"
      @click="isOpen = !isOpen"
    >
      {{ title }}
      <ChevronDown
        :size="16"
        class="text-text-muted transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
      />
    </button>
    <div
      v-show="isOpen"
      class="pb-4 text-sm text-text-secondary leading-relaxed whitespace-pre-line"
    >
      <slot />
    </div>
  </div>
</template>
