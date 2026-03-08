// Keys used in localStorage
const KEYS = {
  ACCESS: 'access_token',
  REFRESH: 'refresh_token',
  USER: 'auth_user', // { id, email, role, full_name }
}

export function saveTokens({ access, refresh, user }) {
  if (access) localStorage.setItem(KEYS.ACCESS, access)
  if (refresh) localStorage.setItem(KEYS.REFRESH, refresh)
  if (user) localStorage.setItem(KEYS.USER, JSON.stringify(user))
}

export function getAccessToken() {
  return localStorage.getItem(KEYS.ACCESS)
}

export function getRefreshToken() {
  return localStorage.getItem(KEYS.REFRESH)
}

export function getSavedUser() {
  try {
    const raw = localStorage.getItem(KEYS.USER)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function clearTokens() {
  localStorage.removeItem(KEYS.ACCESS)
  localStorage.removeItem(KEYS.REFRESH)
  localStorage.removeItem(KEYS.USER)
  // Also clear old session keys for migration
  localStorage.removeItem('customer')
  localStorage.removeItem('staff')
  localStorage.removeItem('manager')
}

/**
 * Parse JWT payload (base64 decode, no verification — server validates).
 * Returns null if token is missing or malformed.
 */
export function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const json = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(json)
  } catch {
    return null
  }
}

/**
 * Returns true if the access token is present and not expired.
 */
export function isTokenValid() {
  const token = getAccessToken()
  if (!token) return false
  const payload = parseJwt(token)
  if (!payload || !payload.exp) return false
  // Add 30-second buffer
  return payload.exp * 1000 > Date.now() + 30_000
}
