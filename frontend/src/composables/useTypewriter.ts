import { ref, watch, onUnmounted, type Ref } from 'vue'

/**
 * Typewriter composable — buffers a source string and releases it
 * character-by-character on a timer for smooth streaming display.
 */
export function useTypewriter(source: Ref<string>, charsPerTick = 2, intervalMs = 30) {
  const displayed = ref('')
  let timer: ReturnType<typeof setInterval> | null = null
  let cursor = 0

  function startTicking() {
    if (timer) return
    timer = setInterval(() => {
      const target = source.value
      if (cursor < target.length) {
        cursor = Math.min(cursor + charsPerTick, target.length)
        displayed.value = target.slice(0, cursor)
      }
    }, intervalMs)
  }

  function stopTicking() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  function flush() {
    displayed.value = source.value
    cursor = source.value.length
    stopTicking()
  }

  function reset() {
    displayed.value = ''
    cursor = 0
    stopTicking()
  }

  watch(source, (val) => {
    if (val && val.length > 0) {
      startTicking()
    } else {
      reset()
    }
  })

  onUnmounted(() => stopTicking())

  return { displayed, flush, reset }
}
