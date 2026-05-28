<script setup lang="ts">
defineProps<{
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
}>()

defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="open" class="fixed inset-0 z-[55] flex items-center justify-center">
        <div class="absolute inset-0 bg-black/60" @click="$emit('cancel')" />
        <div class="relative bg-bg-surface rounded-card border border-white/[0.08] p-6 w-80 shadow-xl">
          <h3 class="text-text-primary font-medium text-sm mb-2">{{ title }}</h3>
          <p class="text-text-secondary text-xs mb-5">{{ message }}</p>
          <div class="flex gap-3 justify-end">
            <button
              class="px-4 py-1.5 rounded-lg bg-white/[0.06] text-text-secondary text-sm hover:bg-white/[0.1] transition-colors"
              @click="$emit('cancel')"
            >
              {{ cancelLabel || '取消' }}
            </button>
            <button
              class="px-4 py-1.5 rounded-lg bg-red-600/80 text-white text-sm hover:bg-red-600 transition-colors"
              @click="$emit('confirm')"
            >
              {{ confirmLabel || '确定' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-enter-active, .dialog-leave-active { transition: opacity 0.2s ease; }
.dialog-enter-from, .dialog-leave-to { opacity: 0; }
</style>
