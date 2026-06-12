<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'
import { RotateCcw, Pencil, Check, X } from 'lucide-vue-next'
import type { ChatMessage } from '@/types/chat'
import { renderMarkdown } from '@/utils/markdown'
import { formatMessageTime } from '@/utils/formatTime'

const props = defineProps<{
  message: ChatMessage
  characterName?: string
  characterAvatar?: string | null
  isLastAssistant?: boolean
  streaming?: boolean
}>()

defineEmits<{
  retry: []
  regenerate: []
  edit: [content: string]
}>()

const renderedContent = computed(() => renderMarkdown(props.message.content))

// ─── Edit mode ────────────────────────────────────────────
const editing = ref(false)
const editContent = ref('')
const editTextarea = ref<HTMLTextAreaElement>()

function startEditing() {
  editContent.value = props.message.content
  editing.value = true
  nextTick(() => {
    const el = editTextarea.value
    if (el) {
      el.style.height = 'auto'
      el.style.height = el.scrollHeight + 'px'
      el.focus()
    }
  })
}

function cancelEditing() {
  editing.value = false
  editContent.value = ''
}
</script>

<template>
  <div
    class="group flex gap-3 px-4 py-2"
    :class="message.role === 'user' ? 'flex-row-reverse' : ''"
  >
    <div v-if="message.role === 'assistant'" class="w-8 h-8 rounded-full overflow-hidden bg-bg-hover shrink-0">
      <img
        v-if="characterAvatar"
        :src="`/api/static/${characterAvatar}`"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-xs font-serif text-accent/40">
        {{ characterName?.[0] || '?' }}
      </div>
    </div>

    <div
      class="max-w-[70%]"
      :class="message.role === 'user' ? 'items-end' : 'items-start'"
    >
      <div
        v-if="message.role === 'assistant' && !message.error"
        class="text-[10px] text-text-muted mb-1 font-serif"
      >
        {{ characterName }}
      </div>

      <!-- Error message -->
      <div v-if="message.error" class="rounded-xl px-4 py-3 bg-red-950/60 border border-red-800/30 text-sm">
        <p class="text-red-300 mb-2">{{ message.content }}</p>
        <button
          class="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 transition-colors"
          @click="$emit('retry')"
        >
          <RotateCcw :size="12" />
          重试
        </button>
      </div>

      <!-- User message: edit mode -->
      <div v-else-if="message.role === 'user' && editing" class="w-full">
        <textarea
          ref="editTextarea"
          v-model="editContent"
          class="w-full rounded-xl px-4 py-2.5 text-sm leading-relaxed bg-bg-surface border border-accent/50 text-text-primary focus:outline-none resize-none"
          @keydown.enter.exact.prevent="editing = false; $emit('edit', editContent)"
          @keydown.escape="cancelEditing"
        />
        <div class="flex items-center gap-2 mt-1.5 justify-end">
          <button
            class="flex items-center gap-1 text-[10px] text-text-muted hover:text-text-secondary transition-colors"
            @click="cancelEditing"
          >
            <X :size="11" />
            取消
          </button>
          <button
            class="flex items-center gap-1 text-[10px] text-accent hover:text-accent-hover transition-colors"
            @click="editing = false; $emit('edit', editContent)"
          >
            <Check :size="11" />
            发送
          </button>
        </div>
      </div>

      <!-- User message: display mode -->
      <div
        v-else-if="message.role === 'user'"
        class="rounded-xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap bg-accent/15 text-text-primary"
      >
        {{ message.content }}
      </div>

      <!-- Assistant message (markdown) -->
      <div
        v-else
        class="rounded-xl rounded-tl-sm px-4 py-2.5 text-sm leading-relaxed bg-bg-surface text-text-primary border border-white/[0.06] markdown-body"
        v-html="renderedContent"
      />

      <!-- Timestamp + action buttons row -->
      <div class="flex items-center gap-2 mt-1" :class="message.role === 'user' ? 'flex-row-reverse' : ''">
        <span class="text-[10px] text-text-muted">
          {{ formatMessageTime(message.created_at) }}
        </span>

        <!-- User message: edit button -->
        <button
          v-if="message.role === 'user' && !editing && !streaming"
          class="opacity-0 group-hover:opacity-100 flex items-center gap-1 text-[10px] text-text-muted hover:text-text-secondary transition-all"
          @click="startEditing"
        >
          <Pencil :size="10" />
        </button>

        <!-- Last assistant message: regenerate button -->
        <button
          v-if="isLastAssistant && !streaming"
          class="opacity-0 group-hover:opacity-100 flex items-center gap-1 text-[10px] text-text-muted hover:text-text-secondary transition-all"
          @click="$emit('regenerate')"
        >
          <RotateCcw :size="10" />
          重新生成
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.markdown-body :deep(p) {
  margin-bottom: 0.5em;
}
.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}
.markdown-body :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 0.75em 1em;
  overflow-x: auto;
  margin: 0.5em 0;
}
.markdown-body :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.85em;
}
.markdown-body :deep(:not(pre) > code) {
  background: rgba(255, 255, 255, 0.06);
  padding: 0.15em 0.4em;
  border-radius: 4px;
}
.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}
.markdown-body :deep(strong) {
  color: #e8e6e3;
}
.markdown-body :deep(blockquote) {
  border-left: 3px solid rgba(201, 168, 85, 0.4);
  padding-left: 1em;
  margin: 0.5em 0;
  color: #8b8994;
}
</style>
