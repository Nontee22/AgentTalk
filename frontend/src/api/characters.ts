import api from '@/api'
import type {
  Character,
  CharacterCreate,
  CharacterSummary,
  CharacterUpdate,
} from '@/types/world'

export async function getCharacters(worldId: string): Promise<CharacterSummary[]> {
  const { data } = await api.get(`/worlds/${worldId}/characters`)
  return data
}

export async function getCharacter(id: string): Promise<Character> {
  const { data } = await api.get(`/characters/${id}`)
  return data
}

export async function createCharacter(
  worldId: string,
  body: CharacterCreate,
): Promise<Character> {
  const { data } = await api.post(`/worlds/${worldId}/characters`, body)
  return data
}

export async function updateCharacter(
  id: string,
  body: CharacterUpdate,
): Promise<Character> {
  const { data } = await api.put(`/characters/${id}`, body)
  return data
}

export async function deleteCharacter(id: string): Promise<void> {
  await api.delete(`/characters/${id}`)
}
