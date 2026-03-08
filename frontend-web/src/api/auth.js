import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

// Separate axios instance (no auth interceptor — avoids circular dependency)
const authApi = axios.create({
  baseURL: `${BASE_URL}/api/gateway/auth`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

/**
 * Login via auth-service.
 * @param {string} email
 * @param {string} password
 * @param {string} role - 'CUSTOMER' | 'STAFF' | 'MANAGER'
 * @returns {{ access: string, refresh: string, user: { id, email, role, full_name } }}
 */
export async function authLogin(email, password, role) {
  const res = await authApi.post('/login/', { email, password, role })
  return res.data
}

/**
 * Refresh access token using refresh token.
 * @param {string} refreshToken
 * @returns {{ access: string }}
 */
export async function authRefresh(refreshToken) {
  const res = await authApi.post('/token/refresh/', { refresh: refreshToken })
  return res.data
}

/**
 * Logout — blacklists the refresh token on the server.
 * Fire-and-forget: errors are swallowed.
 */
export async function authLogout(refreshToken) {
  try {
    await authApi.post('/logout/', { refresh: refreshToken })
  } catch {
    // ignore — token may already be expired
  }
}
