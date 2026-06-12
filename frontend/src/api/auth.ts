import api from '@/api'
import type { LoginRequest, RegisterRequest, TokenResponse, User, UserUpdate } from '@/types/auth'

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const { data: res } = await api.post('/auth/login', data)
  return res
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  const { data: res } = await api.post('/auth/register', data)
  return res
}

export async function refreshToken(token: string): Promise<TokenResponse> {
  const { data: res } = await api.post('/auth/refresh', { refresh_token: token })
  return res
}

export async function getProfile(): Promise<User> {
  const { data } = await api.get('/user/profile')
  return data
}

export async function updateProfile(data: UserUpdate): Promise<User> {
  const { data: res } = await api.put('/user/profile', data)
  return res
}
