import api from '@/api'
import type { PaginatedResponse } from '@/types/common'
import type {
  TagCount,
  WorldBook,
  WorldBookCreate,
  WorldBookSummary,
  WorldBookUpdate,
} from '@/types/world'

export async function getWorlds(params?: {
  page?: number
  page_size?: number
  tag?: string
  search?: string
}): Promise<PaginatedResponse<WorldBookSummary>> {
  const { data } = await api.get('/worlds', { params })
  return data
}

export async function getWorld(id: string): Promise<WorldBook> {
  const { data } = await api.get(`/worlds/${id}`)
  return data
}

export async function createWorld(body: WorldBookCreate): Promise<WorldBook> {
  const { data } = await api.post('/worlds', body)
  return data
}

export async function updateWorld(id: string, body: WorldBookUpdate): Promise<WorldBook> {
  const { data } = await api.put(`/worlds/${id}`, body)
  return data
}

export async function deleteWorld(id: string): Promise<void> {
  await api.delete(`/worlds/${id}`)
}

export async function getTags(): Promise<TagCount[]> {
  const { data } = await api.get('/worlds/tags')
  return data
}
