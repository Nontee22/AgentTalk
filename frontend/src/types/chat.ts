export interface ConversationSummary {
  id: string
  character_id: string
  world_id: string
  title: string | null
  message_count: number
  character_name: string | null
  character_avatar: string | null
  last_message: string | null
  updated_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  error?: boolean
}

export interface ChatStartResponse {
  conversation_id: string
  greeting_message: ChatMessage | null
}

export interface CharacterMemory {
  id: string
  content: string
  category: 'fact' | 'relationship' | 'preference' | 'event'
  importance: number
  created_at: string
  last_accessed_at: string
}

export interface MemoryListResponse {
  memories: CharacterMemory[]
  total: number
}
