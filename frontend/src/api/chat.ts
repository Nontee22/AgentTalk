import api from '@/api'
import type { PaginatedResponse } from '@/types/common'
import type { ChatMessage, ChatStartResponse, ConversationSummary } from '@/types/chat'

export async function startChat(
  characterId: string,
  worldId: string,
): Promise<ChatStartResponse> {
  const { data } = await api.post('/chat/start', {
    character_id: characterId,
    world_id: worldId,
  })
  return data
}

export async function getConversations(): Promise<ConversationSummary[]> {
  const { data } = await api.get('/chat/conversations')
  return data
}

export async function getMessages(
  conversationId: string,
  page = 1,
  pageSize = 50,
): Promise<PaginatedResponse<ChatMessage>> {
  const { data } = await api.get(`/chat/${conversationId}`, {
    params: { page, page_size: pageSize },
  })
  return data
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await api.delete(`/chat/${conversationId}`)
}

export async function stopGeneration(conversationId: string): Promise<void> {
  await api.post(`/chat/${conversationId}/stop`)
}

export function sendMessageSSE(
  conversationId: string,
  content: string,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
  onRetry?: (attempt: number) => void,
  maxRetries = 3,
): AbortController {
  const controller = new AbortController()

  function attempt(retryCount: number) {
    fetch(`/api/chat/${conversationId}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok || !response.body) {
          onError('连接失败')
          return
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const payload = line.slice(6).trim()

            if (payload === '[DONE]') {
              onDone()
              return
            }

            try {
              const parsed = JSON.parse(payload)
              if (parsed.error) {
                onError(parsed.error)
                return
              }
              if (parsed.token) {
                onToken(parsed.token)
              }
            } catch {
              // skip malformed lines
            }
          }
        }
        onDone()
      })
      .catch((err) => {
        if (err.name === 'AbortError') return

        if (retryCount < maxRetries) {
          onRetry?.(retryCount + 1)
          setTimeout(() => attempt(retryCount + 1), 1000)
        } else {
          onError('网络连接失败，已重试 3 次')
        }
      })
  }

  attempt(0)
  return controller
}
