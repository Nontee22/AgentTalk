import { defineStore } from 'pinia'
import { ref } from 'vue'

import { sendMessageSSE, stopGeneration } from '@/api/chat'
import { useConversationStore } from '@/stores/conversationStore'
import { useToast } from '@/composables/useToast'

export const useStreamStore = defineStore('stream', () => {
  const streaming = ref(false)
  const streamingContent = ref('')

  let abortController: AbortController | null = null
  const { showToast } = useToast()

  // ─── Internal: shared streaming logic ───────────────────────

  function _startStream(conversationId: string, content: string) {
    const convStore = useConversationStore()

    streaming.value = true
    streamingContent.value = ''

    abortController = sendMessageSSE(
      conversationId,
      content,
      (token) => {
        streamingContent.value += token
      },
      () => {
        convStore.pushMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: streamingContent.value,
          created_at: new Date().toISOString(),
        })
        streamingContent.value = ''
        streaming.value = false
        convStore.fetchConversations()
      },
      (error) => {
        convStore.pushMessage({
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

  function sendMessage(content: string) {
    const convStore = useConversationStore()
    if (!convStore.currentConversationId || streaming.value) return

    convStore.pushMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    })

    _startStream(convStore.currentConversationId, content)
  }

  function regenerateLastMessage() {
    const convStore = useConversationStore()
    if (!convStore.currentConversationId || streaming.value) return

    let lastAssistantIdx = -1
    for (let i = convStore.messages.length - 1; i >= 0; i--) {
      if (convStore.messages[i].role === 'assistant' && !convStore.messages[i].error) {
        lastAssistantIdx = i
        break
      }
    }
    if (lastAssistantIdx === -1) return

    const lastUserMsg = convStore.messages
      .slice(0, lastAssistantIdx)
      .reverse()
      .find((m) => m.role === 'user')
    if (!lastUserMsg) return

    convStore.messages.splice(lastAssistantIdx, 1)

    _startStream(convStore.currentConversationId, lastUserMsg.content)
  }

  function editAndResend(messageId: string, newContent: string) {
    const convStore = useConversationStore()
    if (!convStore.currentConversationId || streaming.value) return

    const idx = convStore.messages.findIndex((m) => m.id === messageId)
    if (idx === -1) return

    convStore.messages.splice(idx)

    sendMessage(newContent)
  }

  function retryLastMessage() {
    const convStore = useConversationStore()
    const errorIdx = convStore.messages.map((m) => m.error).lastIndexOf(true)
    if (errorIdx === -1) return

    const lastUserMsg = convStore.messages
      .slice(0, errorIdx)
      .reverse()
      .find((m) => m.role === 'user')
    if (!lastUserMsg || !convStore.currentConversationId) return

    convStore.messages.splice(errorIdx, 1)

    _startStream(convStore.currentConversationId, lastUserMsg.content)
  }

  function stopStreaming() {
    const convStore = useConversationStore()

    if (abortController) {
      abortController.abort()
      abortController = null
    }
    if (convStore.currentConversationId) {
      stopGeneration(convStore.currentConversationId).catch(() => {})
    }
    if (streamingContent.value) {
      convStore.pushMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: streamingContent.value,
        created_at: new Date().toISOString(),
      })
    }
    streamingContent.value = ''
    streaming.value = false
  }

  return {
    streaming,
    streamingContent,
    sendMessage,
    regenerateLastMessage,
    editAndResend,
    retryLastMessage,
    stopStreaming,
  }
})
