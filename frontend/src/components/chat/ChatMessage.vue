<script setup lang="ts">
import type { ChatMessage } from '@/types/chat'

defineProps<{
  message: ChatMessage
  characterName?: string
  characterAvatar?: string | null
}>()
</script>

<template>
  <div
    class="flex gap-3 px-4 py-2"
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
        v-if="message.role === 'assistant'"
        class="text-[10px] text-text-muted mb-1 font-serif"
      >
        {{ characterName }}
      </div>
      <div
        class="rounded-xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap"
        :class="
          message.role === 'user'
            ? 'bg-accent/15 text-text-primary rounded-tr-sm'
            : 'bg-bg-surface text-text-primary rounded-tl-sm border border-white/[0.06]'
        "
      >
        {{ message.content }}
      </div>
    </div>
  </div>
</template>
