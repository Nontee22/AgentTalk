import { refreshToken as apiRefresh } from '@/api/auth'

/**
 * Ensure we have a valid (non-expired) access token before SSE fetch.
 * Proactively refreshes if the token expires within 60 seconds.
 * Returns the token string or null if unauthenticated.
 */
export async function ensureFreshToken(): Promise<string | null> {
  let token = localStorage.getItem('access_token')
  if (!token) return null

  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const expiresAt = payload.exp * 1000
    if (Date.now() > expiresAt - 60_000) {
      const rt = localStorage.getItem('refresh_token')
      if (!rt) return null
      const res = await apiRefresh(rt)
      localStorage.setItem('access_token', res.access_token)
      localStorage.setItem('refresh_token', res.refresh_token)
      token = res.access_token
    }
  } catch {
    // If decode fails, just use current token
  }
  return token
}
