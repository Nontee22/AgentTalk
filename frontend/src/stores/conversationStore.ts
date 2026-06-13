import { defineStore } from 'pinia'
import { ref } from 'vue'

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

  async function fetchConversations() {
    conversations.value = await getConversations()
  }

  async function loadMessages(conversationId: string) {
    currentConversationId.value = conversationId
    loading.value = true
    try {
      const data = await getMessages(conversationId)
      messages.value = data.items
    } finally {
      loading.value = false
    }
  }

  async function createConversation(characterId: string, worldId: string) {
    const result = await startChat(characterId, worldId)
    currentConversationId.value = result.conversation_id

    messages.value = []
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
    fetchConversations,
    loadMessages,
    createConversation,
    removeConversation,
    pushMessage,
  }
})
