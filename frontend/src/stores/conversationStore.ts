import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import {
  startChat,
  getConversations,
  getMessages,
  deleteConversation,
} from '@/api/chat'
import type { ChatMessage, ConversationSummary } from '@/types/chat'

export const useConversationStore = defineStore('conversation', () => {
  const conversations = ref<ConversationSummary[]>([])
  const currentConversationId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)

  // Pagination state
  const currentPage = ref(1)
  const totalMessages = ref(0)
  const hasMore = computed(() => currentPage.value * 50 < totalMessages.value)
  const loadingMore = ref(false)

  async function fetchConversations() {
    conversations.value = await getConversations()
  }

  async function loadMessages(conversationId: string) {
    currentConversationId.value = conversationId
    loading.value = true
    try {
      const data = await getMessages(conversationId)
      // Backend returns newest first (DESC), reverse for chronological display
      messages.value = [...data.items].reverse()
      currentPage.value = data.page
      totalMessages.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function loadOlderMessages() {
    if (!hasMore.value || loadingMore.value || !currentConversationId.value) return
    loadingMore.value = true
    try {
      const nextPage = currentPage.value + 1
      const data = await getMessages(currentConversationId.value, nextPage)
      // Reverse and prepend older messages to the beginning
      messages.value = [...data.items.reverse(), ...messages.value]
      currentPage.value = nextPage
      totalMessages.value = data.total
    } finally {
      loadingMore.value = false
    }
  }

  async function createConversation(characterId: string, worldId: string) {
    const result = await startChat(characterId, worldId)
    currentConversationId.value = result.conversation_id

    messages.value = []
    currentPage.value = 1
    totalMessages.value = 0
    if (result.greeting_message) {
      messages.value.push(result.greeting_message)
    }

    await fetchConversations()
    return result.conversation_id
  }

  async function removeConversation(id: string) {
    await deleteConversation(id)
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (currentConversationId.value === id) {
      currentConversationId.value = null
      messages.value = []
      currentPage.value = 1
      totalMessages.value = 0
    }
  }

  function pushMessage(msg: ChatMessage) {
    messages.value.push(msg)
  }

  return {
    conversations,
    currentConversationId,
    messages,
    loading,
    hasMore,
    loadingMore,
    fetchConversations,
    loadMessages,
    loadOlderMessages,
    createConversation,
    removeConversation,
    pushMessage,
  }
})
