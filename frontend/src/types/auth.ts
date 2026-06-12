export interface User {
  id: string
  username: string
  email: string
  nickname: string | null
  avatar: string | null
  is_admin: boolean
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserUpdate {
  nickname?: string
  avatar?: string
}
