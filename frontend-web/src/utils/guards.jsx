import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { isTokenValid } from './token'

export function RequireCustomer({ children }) {
  const { customer } = useAuth()
  if (!customer || !isTokenValid()) return <Navigate to="/login" replace />
  return children
}

export function RequireStaff({ children }) {
  const { staff } = useAuth()
  if (!staff || !isTokenValid()) return <Navigate to="/staff/login" replace />
  return children
}

export function RequireManager({ children }) {
  const { manager } = useAuth()
  if (!manager || !isTokenValid()) return <Navigate to="/manager/login" replace />
  return children
}
