import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export function RequireCustomer({ children }) {
  const { customer } = useAuth()
  if (!customer) return <Navigate to="/login" replace />
  return children
}

export function RequireStaff({ children }) {
  const { staff } = useAuth()
  if (!staff) return <Navigate to="/staff/login" replace />
  return children
}

export function RequireManager({ children }) {
  const { manager } = useAuth()
  if (!manager) return <Navigate to="/manager/login" replace />
  return children
}
