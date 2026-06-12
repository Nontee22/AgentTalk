<script setup lang="ts">
import { onMounted, ref, nextTick, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PanelRight } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chatStore'
import { useMemoryStore } from '@/stores/memoryStore'
import { useEventStream } from '@/composables/useEventStream'
import { getCharacter } from '@/api/characters'
import { getWorld } from '@/api/worlds'
import { renderMarkdown } from '@/utils/markdown'
import ConversationList from '@/components/chat/ConversationList.vue'
import ChatMessageComp from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import CharacterPanel from '@/components/layout/CharacterPanel.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import type { Character, WorldBook } from '@/types/world'

const route = useRoute()
const router = useRouter()
const store = useChatStore()
const memoryStore = useMemoryStore()

const character = ref<Character | null>(null)
const world = ref<WorldBook | null>(null)
const showPanel = ref(true)
const messagesContainer = ref<HTMLDivElement>()
const deleteConfirmOpen = ref(false)
const pendingDeleteId = ref<string | null>(null)

const conversationId = computed(() => route.params.conversationId as string)

const streamingHtml = computed(() => renderMarkdown(store.streamingContent))

const lastAssistantIndex = computed(() => {
  for (let i = store.messages.length - 1; i >= 0; i--) {
    if (store.messages[i].role === 'assistant' && !store.messages[i].error) return i
  }
  return -1
})

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function loadConversationData(convId: string) {
  await store.loadMessages(convId)

  const conv = store.conversations.find((c) => c.id === convId)
  if (conv) {
    character.value = await getCharacter(conv.character_id)
    world.value = await getWorld(conv.world_id)
  }
  scrollToBottom()
}

watch(
  () => store.messages.length,
  () => scrollToBottom(),
)

watch(
  () => store.streamingContent,
  () => scrollToBottom(),
)

watch(
  conversationId,
  async (id) => {
    if (id) await loadConversationData(id)
  },
)

onMounted(async () => {
  await store.fetchConversations()
  if (conversationId.value) {
    await loadConversationData(conversationId.value)
  }
})

// SSE side-channel: listen for real-time events from backend
useEventStream({
  onMemoryReady: (data) => {
    if (data.character_id === character.value?.id) {
      memoryStore.loadMemories(data.character_id)
    }
  },
})

async function handleSelectConversation(id: string) {
  router.push({ name: 'chat', params: { conversationId: id } })
}

function handleSend(content: string) {
  store.sendMessage(content)
  scrollToBottom()
}

async function handleDeleteConversation(id: string) {
  pendingDeleteId.value = id
  deleteConfirmOpen.value = true
}

async function confirmDelete() {
  if (!pendingDeleteId.value) return
  await store.removeConversation(pendingDeleteId.value)
  deleteConfirmOpen.value = false
  pendingDeleteId.value = null
  if (store.conversations.length) {
    router.push({ name: 'chat', params: { conversationId: store.conversations[0].id } })
  } else {
    router.push({ name: 'worlds' })
  }
}

function handleNewChat() {
  router.push({ name: 'worlds' })
}
</script>

<template>
  <div class="h-[calc(100vh-3.5rem)] flex">
    <ConversationList
      :conversations="store.conversations"
      :current-id="conversationId"
      @select="handleSelectConversation"
      @delete="handleDeleteConversation"
      @new-chat="handleNewChat"
    />

    <div class="flex-1 flex flex-col min-w-0">
      <div class="flex items-center justify-between px-4 py-2 border-b border-white/[0.06] bg-bg-deep">
        <div class="flex items-center gap-2">
          <span v-if="world" class="text-text-muted text-xs">{{ world.name }}</span>
          <span v-if="world && character" class="text-text-muted text-xs">&middot;</span>
          <span v-if="character" class="text-text-primary text-sm font-serif">{{ character.name }}</span>
        </div>
        <button
          class="p-1.5 rounded-lg hover:bg-white/[0.06] text-text-muted hover:text-text-primary transition-colors"
          aria-label="切换角色面板"
          @click="showPanel = !showPanel"
        >
          <PanelRight :size="16" />
        </button>
      </div>

      <div v-if="conversationId" class="flex-1 flex flex-col min-h-0">
        <div ref="messagesContainer" class="flex-1 overflow-y-auto py-4 space-y-1">
          <ChatMessageComp
            v-for="(msg, index) in store.messages"
            :key="msg.id"
            :message="msg"
            :character-name="character?.name"
            :character-avatar="character?.avatar"
            :is-last-assistant="msg.role === 'assistant' && !msg.error && index === lastAssistantIndex"
            :streaming="store.streaming"
            @retry="store.retryLastMessage"
            @regenerate="store.regenerateLastMessage"
            @edit="(content: string) => store.editAndResend(msg.id, content)"
          />

          <div v-if="store.streaming" class="flex gap-3 px-4 py-2">
            <div class="w-8 h-8 rounded-full overflow-hidden bg-bg-hover shrink-0">
              <img
                v-if="character?.avatar"
                :src="`/api/static/${character.avatar}`"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-xs font-serif text-accent/40">
                {{ character?.name?.[0] }}
              </div>
            </div>
            <div class="max-w-[70%]">
              <div class="text-[10px] text-text-muted mb-1 font-serif">{{ character?.name }}</div>
              <div
                class="rounded-xl rounded-tl-sm px-4 py-2.5 text-sm leading-relaxed bg-bg-surface text-text-primary border border-white/[0.06] markdown-body"
              >
                <span v-html="streamingHtml" /><span class="inline-block w-0.5 h-4 bg-accent animate-blink ml-0.5 align-text-bottom" />
              </div>
            </div>
          </div>
        </div>

        <ChatInput
          :streaming="store.streaming"
          @send="handleSend"
          @stop="store.stopStreaming"
        />
      </div>

      <div v-else class="flex-1 flex items-center justify-center">
        <div class="text-center text-text-muted">
          <p class="text-sm">选择一个对话或从世界书中开始新对话</p>
        </div>
      </div>
    </div>

    <CharacterPanel
      v-if="showPanel"
      :character="character"
      :world="world"
      @close="showPanel = false"
    />
    <ConfirmDialog
      :open="deleteConfirmOpen"
      title="删除对话"
      message="确定要删除这个对话吗？此操作不可恢复。"
      confirm-label="删除"
      @confirm="confirmDelete"
      @cancel="deleteConfirmOpen = false"
    />
  </div>
</template>

<style scoped>
.markdown-body :deep(p) { margin-bottom: 0.5em; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 0.75em 1em;
  overflow-x: auto;
  margin: 0.5em 0;
}
.markdown-body :deep(code) { font-family: 'Consolas', 'Monaco', monospace; font-size: 0.85em; }
.markdown-body :deep(:not(pre) > code) {
  background: rgba(255, 255, 255, 0.06);
  padding: 0.15em 0.4em;
  border-radius: 4px;
}
</style>
