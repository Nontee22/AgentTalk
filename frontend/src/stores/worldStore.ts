import { defineStore } from 'pinia'
import { ref } from 'vue'

import { getWorlds, getWorld, createWorld, updateWorld, deleteWorld, getTags } from '@/api/worlds'
import { getCharacters } from '@/api/characters'
import type { WorldBook, WorldBookCreate, WorldBookSummary, WorldBookUpdate, TagCount } from '@/types/world'
import type { CharacterSummary } from '@/types/world'

export const useWorldStore = defineStore('world', () => {
  const worlds = ref<WorldBookSummary[]>([])
  const currentWorld = ref<WorldBook | null>(null)
  const characters = ref<CharacterSummary[]>([])
  const tags = ref<TagCount[]>([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchWorlds(params?: {
    page?: number
    page_size?: number
    tag?: string
    search?: string
  }) {
    loading.value = true
    try {
      const data = await getWorlds(params)
      worlds.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchTags() {
    try {
      tags.value = await getTags()
    } catch {
      tags.value = []
    }
  }

  async function fetchWorldDetail(id: string) {
    loading.value = true
    try {
      currentWorld.value = await getWorld(id)
      characters.value = await getCharacters(id)
    } finally {
      loading.value = false
    }
  }

  async function addWorld(data: WorldBookCreate) {
    return await createWorld(data)
  }

  async function editWorld(id: string, data: WorldBookUpdate) {
    return await updateWorld(id, data)
  }

  async function removeWorld(id: string) {
    await deleteWorld(id)
    worlds.value = worlds.value.filter((w) => w.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  return {
    worlds,
    currentWorld,
    characters,
    tags,
    total,
    loading,
    fetchWorlds,
    fetchTags,
    fetchWorldDetail,
    addWorld,
    editWorld,
    removeWorld,
  }
})
