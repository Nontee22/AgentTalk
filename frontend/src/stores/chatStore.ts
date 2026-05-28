import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  startChat,
  getConversations,
  getMessages,
  deleteConversation,
  sendMessageSSE,
} from '@/api/chat'
import type { ChatMessage, ConversationSummary } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<ConversationSummary[]>([])
  const currentConversationId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const streaming = ref(false)
  const streamingContent = ref('')
  const loading = ref(false)

  let abortController: AbortController | null = null

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

  function sendMessage(content: string) {
    if (!currentConversationId.value || streaming.value) return

    messages.value.push({
      id: crypto.randomUUID(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    })

    streaming.value = true
    streamingContent.value = ''

    abortController = sendMessageSSE(
      currentConversationId.value,
      content,
      (token) => {
        streamingContent.value += token
      },
      () => {
        messages.value.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: streamingContent.value,
          created_at: new Date().toISOString(),
        })
        streamingContent.value = ''
        streaming.value = false
        fetchConversations()
      },
      (error) => {
        messages.value.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `[错误] ${error}`,
          created_at: new Date().toISOString(),
        })
        streamingContent.value = ''
        streaming.value = false
      },
    )
  }

  function stopStreaming() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    if (streamingContent.value) {
      messages.value.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: streamingContent.value,
        created_at: new Date().toISOString(),
      })
    }
    streamingContent.value = ''
    streaming.value = false
  }

  async function removeConversation(id: string) {
    await deleteConversation(id)
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (currentConversationId.value === id) {
      currentConversationId.value = null
      messages.value = []
    }
  }

  return {
    conversations,
    currentConversationId,
    messages,
    streaming,
    streamingContent,
    loading,
    fetchConversations,
    loadMessages,
    createConversation,
    sendMessage,
    stopStreaming,
    removeConversation,
  }
})
