import { ref, onUnmounted } from 'vue'
import { refreshToken as apiRefresh } from '@/api/auth'

export interface EventStreamCallbacks {
  onMemoryReady?: (data: { character_id: string }) => void
}

/**
 * Composable that connects to /api/events/stream SSE endpoint.
 * Uses fetch + ReadableStream (not EventSource) to support Authorization header.
 * Auto-reconnects on disconnect with 3s delay.
 */
export function useEventStream(callbacks: EventStreamCallbacks) {
  const connected = ref(false)
  let abortController: AbortController | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let stopped = false

  async function getToken(): Promise<string | null> {
    let token = localStorage.getItem('access_token')
    if (!token) return null

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (Date.now() > payload.exp * 1000 - 60_000) {
        const rt = localStorage.getItem('refresh_token')
        if (!rt) return null
        const res = await apiRefresh(rt)
        localStorage.setItem('access_token', res.access_token)
        localStorage.setItem('refresh_token', res.refresh_token)
        token = res.access_token
      }
    } catch {
      // decode failed, use as-is
    }
    return token
  }

  function dispatchEvent(eventType: string, data: any) {
    if (eventType === 'memory_ready' && callbacks.onMemoryReady) {
      callbacks.onMemoryReady(data)
    }
  }

  async function connect() {
    if (stopped) return

    const token = await getToken()
    if (!token) {
      scheduleReconnect()
      return
    }

    abortController = new AbortController()

    try {
      const response = await fetch('/api/events/stream', {
        headers: { Authorization: `Bearer ${token}` },
        signal: abortController.signal,
      })

      if (!response.ok || !response.body) {
        scheduleReconnect()
        return
      }

      connected.value = true
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = 'message'
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const rawData = line.slice(6).trim()
            try {
              const data = JSON.parse(rawData)
              dispatchEvent(currentEvent, data)
            } catch {
              // skip malformed data
            }
            currentEvent = 'message'
          }
          // skip comments (lines starting with ':') and empty lines
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return
    } finally {
      connected.value = false
    }

    // Connection closed, reconnect
    if (!stopped) {
      scheduleReconnect()
    }
  }

  function scheduleReconnect() {
    if (stopped || reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, 3000)
  }

  function disconnect() {
    stopped = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  }

  // Start connection immediately
  connect()

  // Cleanup on component unmount
  onUnmounted(disconnect)

  return { connected, disconnect }
}
