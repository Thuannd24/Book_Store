import axios from 'axios'
import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from '../utils/token'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

// Request interceptor: attach JWT access token
api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Response interceptor: auto-refresh on 401
let _refreshing = false
let _pendingQueue = []

function flushQueue(error, token = null) {
  _pendingQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token)))
  _pendingQueue = []
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      const refreshToken = getRefreshToken()

      if (!refreshToken) {
        clearTokens()
        window.dispatchEvent(new CustomEvent('auth:logout'))
        return Promise.reject(new Error('Session expired. Please log in again.'))
      }

      if (_refreshing) {
        return new Promise((resolve, reject) => _pendingQueue.push({ resolve, reject }))
          .then((newToken) => {
            original.headers['Authorization'] = `Bearer ${newToken}`
            return api(original)
          })
          .catch((err) => Promise.reject(err))
      }

      original._retry = true
      _refreshing = true

      try {
        const resp = await axios.post(
          `${BASE_URL}/api/gateway/auth/token/refresh/`,
          { refresh: refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        )
        const newAccess = resp.data.access
        saveTokens({ access: newAccess })
        original.headers['Authorization'] = `Bearer ${newAccess}`
        flushQueue(null, newAccess)
        return api(original)
      } catch (err) {
        flushQueue(err)
        clearTokens()
        window.dispatchEvent(new CustomEvent('auth:logout'))
        return Promise.reject(new Error('Session expired. Please log in again.'))
      } finally {
        _refreshing = false
      }
    }

    const message =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      'Unknown error'
    return Promise.reject(new Error(message))
  }
)

export default api
