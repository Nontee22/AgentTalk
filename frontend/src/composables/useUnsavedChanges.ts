import { onMounted, onUnmounted, type Ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

/**
 * Composable that warns users before leaving a page with unsaved changes.
 * Intercepts both vue-router navigation and browser tab close/refresh.
 */
export function useUnsavedChanges(isDirty: Ref<boolean>) {
  // Intercept in-app navigation
  onBeforeRouteLeave(() => {
    if (isDirty.value) {
      return window.confirm('有未保存的更改，确定要离开吗？')
    }
    return true
  })

  // Intercept browser close/refresh
  function handleBeforeUnload(e: BeforeUnloadEvent) {
    if (isDirty.value) {
      e.preventDefault()
    }
  }

  onMounted(() => window.addEventListener('beforeunload', handleBeforeUnload))
  onUnmounted(() => window.removeEventListener('beforeunload', handleBeforeUnload))
}
