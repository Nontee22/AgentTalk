import { defineStore } from 'pinia'
import { ref } from 'vue'

import { getCharacterMemories, deleteMemory as apiDeleteMemory } from '@/api/memory'
import type { CharacterMemory } from '@/types/chat'

export const useMemoryStore = defineStore('memory', () => {
  const memories = ref<CharacterMemory[]>([])
  const loading = ref(false)
  const currentCharacterId = ref<string | null>(null)

  async function loadMemories(characterId: string) {
    currentCharacterId.value = characterId
    loading.value = true
    try {
      const res = await getCharacterMemories(characterId)
      memories.value = res.memories
    } catch {
      memories.value = []
    } finally {
      loading.value = false
    }
  }

  async function removeMemory(memoryId: string) {
    await apiDeleteMemory(memoryId)
    memories.value = memories.value.filter((m) => m.id !== memoryId)
  }

  function invalidate() {
    memories.value = []
    currentCharacterId.value = null
  }

  return { memories, loading, currentCharacterId, loadMemories, removeMemory, invalidate }
})
