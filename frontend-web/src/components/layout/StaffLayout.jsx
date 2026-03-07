import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { AdminLayout } from './AdminLayout'

const links = [
  { to: '/staff/books', label: '📚 Books', end: false },
  { to: '/staff/categories', label: '🏷️ Categories', end: false },
]

export function StaffLayout() {
  const { staff, logoutStaff } = useAuth()
  const navigate = useNavigate()
  return (
    <AdminLayout
      panelLabel="Staff Panel"
      links={links}
      user={staff}
      onLogout={() => { logoutStaff(); navigate('/staff/login') }}
    />
  )
}
