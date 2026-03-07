import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { AdminLayout } from './AdminLayout'

const links = [
  { to: '/manager/dashboard', label: '📊 Dashboard', end: false },
]

export function ManagerLayout() {
  const { manager, logoutManager } = useAuth()
  const navigate = useNavigate()
  return (
    <AdminLayout
      panelLabel="Manager Panel"
      links={links}
      user={manager}
      onLogout={() => { logoutManager(); navigate('/manager/login') }}
    />
  )
}
