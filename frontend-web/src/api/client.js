import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

// NOTE: This app uses session-based auth stored in localStorage (no JWT).
// User objects are stored under keys: 'customer', 'staff', 'manager'.
// If JWT is added in the future, attach it here via a request interceptor.

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      'Unknown error'
    return Promise.reject(new Error(message))
  }
)

export default api
