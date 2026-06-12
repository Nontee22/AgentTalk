import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  startChat,
  getConversations,
  getMessages,
  deleteConversation,
  sendMessageSSE,
  stopGeneration,
} from '@/api/chat'
import { useToast } from '@/composables/useToast'
import type { ChatMessage, ConversationSummary } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<ConversationSummary[]>([])
  const currentConversationId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const streaming = ref(false)
  const streamingContent = ref('')
  const loading = ref(false)

  let abortController: AbortController | null = null
  const { showToast } = useToast()

  // ─── Internal: shared streaming logic ───────────────────────

  function _startStream(conversationId: string, content: string) {
    streaming.value = true
    streamingContent.value = ''

    abortController = sendMessageSSE(
      conversationId,
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
          content: error,
          created_at: new Date().toISOString(),
          error: true,
        })
        streamingContent.value = ''
        streaming.value = false
      },
      (attempt) => {
        showToast(`连接断开，正在重试 (${attempt}/3)...`, 'info')
      },
    )
  }

  // ─── Public methods ─────────────────────────────────────────

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

    _startStream(currentConversationId.value, content)
  }

  function regenerateLastMessage() {
    if (!currentConversationId.value || streaming.value) return

    // 找最后一条非 error 的 assistant 消息
    let lastAssistantIdx = -1
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'assistant' && !messages.value[i].error) {
        lastAssistantIdx = i
        break
      }
    }
    if (lastAssistantIdx === -1) return

    // 找其前面最近的 user 消息
    const lastUserMsg = messages.value
      .slice(0, lastAssistantIdx)
      .reverse()
      .find((m) => m.role === 'user')
    if (!lastUserMsg) return

    // 移除 assistant 消息（保留 user 消息）
    messages.value.splice(lastAssistantIdx, 1)

    _startStream(currentConversationId.value, lastUserMsg.content)
  }

  function editAndResend(messageId: string, newContent: string) {
    if (!currentConversationId.value || streaming.value) return

    const idx = messages.value.findIndex((m) => m.id === messageId)
    if (idx === -1) return

    // 删除该消息及其后所有消息
    messages.value.splice(idx)

    // 用新内容重新发送
    sendMessage(newContent)
  }

  function retryLastMessage() {
    const errorIdx = messages.value.map((m) => m.error).lastIndexOf(true)
    if (errorIdx === -1) return

    // Find the user message that triggered the error
    const lastUserMsg = messages.value
      .slice(0, errorIdx)
      .reverse()
      .find((m) => m.role === 'user')
    if (!lastUserMsg || !currentConversationId.value) return

    // Remove only the error message, keep the user message
    messages.value.splice(errorIdx, 1)

    _startStream(currentConversationId.value, lastUserMsg.content)
  }

  function stopStreaming() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    if (currentConversationId.value) {
      stopGeneration(currentConversationId.value).catch(() => {})
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
    regenerateLastMessage,
    editAndResend,
    retryLastMessage,
    stopStreaming,
    removeConversation,
  }
})
