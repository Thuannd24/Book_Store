import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { useState, useRef, useEffect } from 'react'

export function CustomerNavbar() {
  const { customer, logoutCustomer } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const profileRef = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

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
              <NavLink to="/reviews" className={navLinkClass}>My Reviews</NavLink>
            </>
          )}
        </div>

        {/* User actions */}
        <div className="hidden md:flex items-center gap-3">
          {customer ? (
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen((o) => !o)}
                className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-indigo-600 transition-colors"
              >
                <span className="bg-indigo-100 text-indigo-700 rounded-full h-8 w-8 flex items-center justify-center font-bold text-xs shrink-0">
                  {customer.full_name?.charAt(0).toUpperCase()}
                </span>
                <span className="max-w-[120px] truncate">{customer.full_name}</span>
                <span className="text-gray-400 text-xs">{profileOpen ? '▲' : '▼'}</span>
              </button>
              {/* Dropdown */}
              <div
                className={`absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border text-sm z-50
                  transition-all duration-150 origin-top-right
                  ${profileOpen ? 'opacity-100 scale-100 pointer-events-auto' : 'opacity-0 scale-95 pointer-events-none'}`}
              >
                <div className="px-4 py-3 border-b">
                  <p className="text-xs text-gray-400">Signed in as</p>
                  <p className="font-medium text-gray-700 truncate">{customer.email}</p>
                </div>
                <div className="py-1">
                  <Link
                    to="/profile"
                    onClick={() => setProfileOpen(false)}
                    className="block px-4 py-2 text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    👤 My Profile
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 transition-colors"
                  >
                    🚪 Logout
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <>
              <Link to="/login" className="text-sm text-gray-600 hover:text-indigo-600 font-medium transition-colors">Login</Link>
              <Link to="/register" className="bg-indigo-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-indigo-700 font-medium transition-colors">Register</Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 text-gray-600 hover:text-indigo-600 transition-colors"
          onClick={() => setMobileOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile menu — animated slide */}
      <div
        className={`md:hidden bg-white border-t overflow-hidden transition-all duration-300 ease-in-out
          ${mobileOpen ? 'max-h-80 opacity-100' : 'max-h-0 opacity-0'}`}
      >
        <div className="px-4 py-3 flex flex-col gap-1">
          <NavLink to="/" end className="text-sm text-gray-700 py-2 px-2 rounded-lg hover:bg-gray-50" onClick={() => setMobileOpen(false)}>🏠 Home</NavLink>
          <NavLink to="/books" className="text-sm text-gray-700 py-2 px-2 rounded-lg hover:bg-gray-50" onClick={() => setMobileOpen(false)}>📚 Books</NavLink>
          {customer ? (
            <>
              <NavLink to="/cart" className="text-sm text-gray-700 py-2 px-2 rounded-lg hover:bg-gray-50" onClick={() => setMobileOpen(false)}>🛒 Cart</NavLink>
              <NavLink to="/orders" className="text-sm text-gray-700 py-2 px-2 rounded-lg hover:bg-gray-50" onClick={() => setMobileOpen(false)}>📦 Orders</NavLink>
              <NavLink to="/recommendations" className="text-sm text-gray-700 py-2 px-2 rounded-lg hover:bg-gray-50" onClick={() => setMobileOpen(false)}>✨ For You</NavLink>
              <NavLink to="/reviews" className="text-sm text-gray-700 py-2 px-2 rounded-lg hover:bg-gray-50" onClick={() => setMobileOpen(false)}>⭐ My Reviews</NavLink>
              <NavLink to="/profile" className="text-sm text-gray-700 py-2 px-2 rounded-lg hover:bg-gray-50" onClick={() => setMobileOpen(false)}>👤 My Profile</NavLink>
              <button onClick={() => { handleLogout(); setMobileOpen(false) }} className="text-sm text-red-600 text-left py-2 px-2 rounded-lg hover:bg-red-50">🚪 Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm text-gray-700 py-2 px-2 rounded-lg hover:bg-gray-50" onClick={() => setMobileOpen(false)}>Login</Link>
              <Link to="/register" className="text-sm text-indigo-600 font-medium py-2 px-2 rounded-lg hover:bg-indigo-50" onClick={() => setMobileOpen(false)}>Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
