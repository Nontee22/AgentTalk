export interface WorldBook {
  id: string
  name: string
  description: string | null
  setting: string | null
  rules: string | null
  lore: string | null
  factions: string[] | null
  tags: string[] | null
  cover_image: string | null
  is_preset: boolean
  created_by: string | null
  character_count: number
  created_at: string
  updated_at: string
}

export interface WorldBookSummary {
  id: string
  name: string
  description: string | null
  tags: string[] | null
  cover_image: string | null
  is_preset: boolean
  created_by: string | null
  character_count: number
  created_at: string
}

export interface TagCount {
  name: string
  count: number
}

export interface WorldBookCreate {
  name: string
  description?: string
  setting?: string
  rules?: string
  lore?: string
  factions?: string[]
  tags?: string[]
  cover_image?: string
  is_preset?: boolean
}

export interface WorldBookUpdate {
  name?: string
  description?: string
  setting?: string
  rules?: string
  lore?: string
  factions?: string[]
  tags?: string[]
  cover_image?: string
  is_preset?: boolean
}

export interface Character {
  id: string
  world_id: string
  name: string
  avatar: string | null
  identity: string | null
  personality: string | null
  background: string | null
  relationships: string | null
  language_style: string | null
  knowledge: string | null
  greeting: string | null
  tags: string[] | null
  created_at: string
  updated_at: string
}

export interface CharacterSummary {
  id: string
  name: string
  avatar: string | null
  identity: string | null
  tags: string[] | null
}

export interface CharacterCreate {
  name: string
  avatar?: string
  identity?: string
  personality?: string
  background?: string
  relationships?: string
  language_style?: string
  knowledge?: string
  greeting?: string
  tags?: string[]
}

export interface CharacterUpdate {
  name?: string
  avatar?: string
  identity?: string
  personality?: string
  background?: string
  relationships?: string
  language_style?: string
  knowledge?: string
  greeting?: string
  tags?: string[]
}
