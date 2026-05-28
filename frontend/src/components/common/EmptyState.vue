<script setup lang="ts">
import { PackageOpen } from 'lucide-vue-next'

defineProps<{
  message: string
  actionLabel?: string
}>()

defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-20 text-center">
    <PackageOpen :size="48" class="text-text-muted mb-4" />
    <p class="text-text-secondary text-sm mb-4">{{ message }}</p>
    <button
      v-if="actionLabel"
      class="px-4 py-2 rounded-lg bg-accent text-bg-deep text-sm font-medium hover:bg-accent-hover transition-colors"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
