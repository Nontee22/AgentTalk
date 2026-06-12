import api from '@/api'
import type { MemoryListResponse } from '@/types/chat'

export async function getCharacterMemories(characterId: string): Promise<MemoryListResponse> {
  const { data } = await api.get(`/memories/character/${characterId}`)
  return data
}

export async function deleteMemory(memoryId: string): Promise<void> {
  await api.delete(`/memories/${memoryId}`)
}
