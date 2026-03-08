import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { saveTokens, clearTokens, getSavedUser, getRefreshToken } from '../utils/token'
import { authLogout } from '../api/auth'

const AuthContext = createContext(null)

/**
 * Determine current role from stored user.
 * Returns: 'CUSTOMER' | 'STAFF' | 'MANAGER' | null
 */
function getRoleFromUser(user) {
  if (!user) return null
  return user.role || null
}

export function AuthProvider({ children }) {
  const [authUser, setAuthUser] = useState(() => getSavedUser())

  // Derived role shortcuts (kept for backward compatibility with existing components)
  const role = getRoleFromUser(authUser)
  const customer = role === 'CUSTOMER' ? authUser : null
  const staff = role === 'STAFF' ? authUser : null
  const manager = role === 'MANAGER' ? authUser : null

  // Listen for forced logout event (triggered by api/client.js on token refresh failure)
  useEffect(() => {
    const handleForcedLogout = () => {
      setAuthUser(null)
    }
    window.addEventListener('auth:logout', handleForcedLogout)
    return () => window.removeEventListener('auth:logout', handleForcedLogout)
  }, [])

  /**
   * Called after successful auth-service login.
   * auth-service returns: { access, refresh, user_id, email, role }
   * Normalizes to user object: { id, email, role, full_name }
   */
  const loginWithTokens = useCallback((data) => {
    // Support both { user: {...} } and flat { user_id, email, role } shapes
    const user = data.user ?? {
      id: data.user_id,
      email: data.email,
      role: data.role,
      full_name: data.full_name || data.email,
    }
    saveTokens({ access: data.access, refresh: data.refresh, user })
    setAuthUser(user)
  }, [])

  const logout = useCallback(async () => {
    const refresh = getRefreshToken()
    if (refresh) {
      await authLogout(refresh) // fire-and-forget blacklist on server
    }
    clearTokens()
    setAuthUser(null)
  }, [])

  // Backward-compatible aliases used by existing login pages
  const loginAsCustomer = useCallback((data) => loginWithTokens(data), [loginWithTokens])
  const loginAsStaff = useCallback((data) => loginWithTokens(data), [loginWithTokens])
  const loginAsManager = useCallback((data) => loginWithTokens(data), [loginWithTokens])
  const logoutCustomer = logout
  const logoutStaff = logout
  const logoutManager = logout

  return (
    <AuthContext.Provider
      value={{
        // New unified API
        authUser,
        role,
        loginWithTokens,
        logout,
        // Backward-compatible aliases
        customer,
        staff,
        manager,
        loginAsCustomer,
        logoutCustomer,
        loginAsStaff,
        logoutStaff,
        loginAsManager,
        logoutManager,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}