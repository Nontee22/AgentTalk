<script setup lang="ts">
import { useToast } from '@/composables/useToast'
import { X, AlertCircle, CheckCircle, Info } from 'lucide-vue-next'

const { toasts, removeToast } = useToast()
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-16 right-4 z-[60] flex flex-col gap-2 w-80">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="flex items-start gap-3 rounded-lg px-4 py-3 shadow-lg border backdrop-blur-sm"
          :class="{
            'bg-bg-surface/95 border-white/[0.08] text-text-primary': toast.type === 'info',
            'bg-red-950/90 border-red-800/40 text-red-200': toast.type === 'error',
            'bg-green-950/90 border-green-800/40 text-green-200': toast.type === 'success',
          }"
        >
          <Info v-if="toast.type === 'info'" :size="16" class="mt-0.5 shrink-0 text-accent" />
          <AlertCircle v-else-if="toast.type === 'error'" :size="16" class="mt-0.5 shrink-0 text-red-400" />
          <CheckCircle v-else :size="16" class="mt-0.5 shrink-0 text-green-400" />
          <p class="flex-1 text-sm">{{ toast.message }}</p>
          <button class="shrink-0 opacity-50 hover:opacity-100" @click="removeToast(toast.id)">
            <X :size="14" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease;
}
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}
.toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
