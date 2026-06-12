<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Send, Square } from 'lucide-vue-next'

defineProps<{
  streaming: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
  stop: []
}>()

const input = ref('')
const textarea = ref<HTMLTextAreaElement>()
const maxLength = 5000

function autoResize() {
  const el = textarea.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 128) + 'px'
}

function handleSubmit() {
  const content = input.value.trim()
  if (!content) return
  emit('send', content)
  input.value = ''
  nextTick(autoResize)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}
</script>

<template>
  <div class="border-t border-white/[0.06] bg-bg-deep p-4">
    <form class="flex items-end gap-3" @submit.prevent="handleSubmit">
      <div class="flex-1 relative">
        <textarea
          ref="textarea"
          v-model="input"
          rows="1"
          :maxlength="maxLength"
          :disabled="disabled"
          placeholder="输入你想说的话..."
          class="w-full rounded-xl bg-bg-surface border border-white/[0.08] px-4 py-2.5 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50 transition-colors resize-none max-h-32"
          @keydown="handleKeydown"
          @input="autoResize"
        />
        <span
          v-if="input.length > maxLength * 0.8"
          class="absolute right-2 bottom-1 text-[10px]"
          :class="input.length >= maxLength ? 'text-red-400' : 'text-text-muted'"
        >
          {{ input.length }}/{{ maxLength }}
        </span>
      </div>

      <button
        v-if="streaming"
        type="button"
        class="p-2.5 rounded-xl bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
        @click="$emit('stop')"
      >
        <Square :size="16" />
      </button>
      <button
        v-else
        type="submit"
        :disabled="!input.trim() || disabled"
        class="p-2.5 rounded-xl bg-accent text-bg-deep hover:bg-accent-hover transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <Send :size="16" />
      </button>
    </form>
  </div>
</template>
