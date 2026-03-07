import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

const loadUser = (key) => {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [customer, setCustomer] = useState(() => loadUser('customer'))
  const [staff, setStaff] = useState(() => loadUser('staff'))
  const [manager, setManager] = useState(() => loadUser('manager'))

  const loginAsCustomer = useCallback((user) => {
    localStorage.setItem('customer', JSON.stringify(user))
    setCustomer(user)
  }, [])

  const logoutCustomer = useCallback(() => {
    localStorage.removeItem('customer')
    setCustomer(null)
  }, [])

  const loginAsStaff = useCallback((user) => {
    localStorage.setItem('staff', JSON.stringify(user))
    setStaff(user)
  }, [])

  const logoutStaff = useCallback(() => {
    localStorage.removeItem('staff')
    setStaff(null)
  }, [])

  const loginAsManager = useCallback((user) => {
    localStorage.setItem('manager', JSON.stringify(user))
    setManager(user)
  }, [])

  const logoutManager = useCallback(() => {
    localStorage.removeItem('manager')
    setManager(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
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
