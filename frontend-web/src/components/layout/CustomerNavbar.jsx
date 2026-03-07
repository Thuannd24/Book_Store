import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { useState } from 'react'

export function CustomerNavbar() {
  const { customer, logoutCustomer } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)

  const handleLogout = () => {
    logoutCustomer()
    setProfileOpen(false)
    navigate('/')
  }

  const navLinkClass = ({ isActive }) =>
    `text-sm font-medium px-1 py-0.5 border-b-2 transition-colors ${
      isActive
        ? 'border-indigo-600 text-indigo-700'
        : 'border-transparent text-gray-600 hover:text-indigo-600'
    }`

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-bold text-indigo-700 text-lg">
          📚 BookStore
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-6">
          <NavLink to="/" end className={navLinkClass}>Home</NavLink>
          <NavLink to="/books" className={navLinkClass}>Books</NavLink>
          {customer && (
            <>
              <NavLink to="/cart" className={navLinkClass}>🛒 Cart</NavLink>
              <NavLink to="/orders" className={navLinkClass}>Orders</NavLink>
              <NavLink to="/recommendations" className={navLinkClass}>For You</NavLink>
            </>
          )}
        </div>

        {/* User actions */}
        <div className="hidden md:flex items-center gap-3">
          {customer ? (
            <div className="relative">
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-indigo-600"
              >
                <span className="bg-indigo-100 text-indigo-700 rounded-full h-8 w-8 flex items-center justify-center font-bold text-xs">
                  {customer.full_name?.charAt(0).toUpperCase()}
                </span>
                {customer.full_name}
              </button>
              {profileOpen && (
                <div className="absolute right-0 mt-2 w-44 bg-white rounded-lg shadow-lg border text-sm z-50">
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-gray-600 hover:text-indigo-600 font-medium"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="bg-indigo-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-indigo-700 font-medium"
              >
                Register
              </Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 text-gray-600"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          ☰
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t px-4 py-3 flex flex-col gap-3">
          <NavLink to="/" end className="text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Home</NavLink>
          <NavLink to="/books" className="text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Books</NavLink>
          {customer ? (
            <>
              <NavLink to="/cart" className="text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Cart</NavLink>
              <NavLink to="/orders" className="text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Orders</NavLink>
              <NavLink to="/recommendations" className="text-sm text-gray-700" onClick={() => setMobileOpen(false)}>For You</NavLink>
              <button onClick={handleLogout} className="text-sm text-red-600 text-left">Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Login</Link>
              <Link to="/register" className="text-sm text-indigo-600 font-medium" onClick={() => setMobileOpen(false)}>Register</Link>
            </>
          )}
        </div>
      )}
    </nav>
  )
}
