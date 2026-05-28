<script setup lang="ts">
import type { ConversationSummary } from '@/types/chat'
import { MessageCircle, Trash2, Search } from 'lucide-vue-next'
import { ref } from 'vue'
import { formatRelativeTime } from '@/utils/formatTime'

defineProps<{
  conversations: ConversationSummary[]
  currentId: string | null
}>()

defineEmits<{
  select: [id: string]
  delete: [id: string]
  newChat: []
}>()

const searchQuery = ref('')
</script>

<template>
  <aside class="w-60 border-r border-white/[0.06] bg-bg-deep flex flex-col h-full">
    <div class="p-3">
      <div class="relative">
        <Search :size="14" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索对话..."
          class="w-full rounded-lg bg-bg-surface border border-white/[0.08] pl-8 pr-3 py-1.5 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-accent/50"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-2 space-y-0.5">
      <button
        v-for="conv in conversations.filter(
          (c) =>
            !searchQuery ||
            c.title?.includes(searchQuery) ||
            c.character_name?.includes(searchQuery),
        )"
        :key="conv.id"
        class="w-full text-left rounded-lg px-3 py-2.5 transition-colors group"
        :class="
          currentId === conv.id
            ? 'bg-bg-surface border-l-2 border-accent'
            : 'hover:bg-bg-surface/50'
        "
        @click="$emit('select', conv.id)"
      >
        <div class="flex items-start gap-2.5">
          <div class="w-8 h-8 rounded-full overflow-hidden bg-bg-hover shrink-0 mt-0.5">
            <img
              v-if="conv.character_avatar"
              :src="`/api/static/${conv.character_avatar}`"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-xs font-serif text-accent/40">
              {{ conv.character_name?.[0] || '?' }}
            </div>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="text-text-primary text-xs font-medium truncate">
                {{ conv.character_name || '未知角色' }}
              </span>
              <button
                class="opacity-0 group-hover:opacity-100 p-0.5 text-text-muted hover:text-red-400 transition-all"
                @click.stop="$emit('delete', conv.id)"
              >
                <Trash2 :size="12" />
              </button>
            </div>
            <p class="text-text-muted text-[10px] truncate mt-0.5">
              {{ conv.last_message || '...' }}
            </p>
            <p class="text-text-muted text-[9px] mt-0.5">
              {{ formatRelativeTime(conv.updated_at) }}
            </p>
          </div>
        </div>
      </button>
    </div>

    <div class="p-3 border-t border-white/[0.06]">
      <button
        class="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-white/[0.06] text-text-secondary text-xs hover:bg-white/[0.1] transition-colors"
        @click="$emit('newChat')"
      >
        <MessageCircle :size="14" />
        新对话
      </button>
    </div>
  </aside>
</template>
