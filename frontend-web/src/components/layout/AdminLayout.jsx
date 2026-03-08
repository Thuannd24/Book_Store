import { NavLink, Outlet } from 'react-router-dom'

/**
 * Shared sidebar layout for Staff and Manager panels.
 * Props:
 *   panelLabel   – e.g. "Staff Panel"
 *   links        – [{ to, label, end }]
 *   user         – logged-in user object (expects .full_name)
 *   onLogout     – callback: logouts + navigates
 */
export function AdminLayout({ panelLabel, links, user, onLogout }) {
  return (
    <div className="min-h-screen flex bg-gray-100">
      <aside className="w-60 bg-white border-r shadow-sm flex flex-col sticky top-0 h-screen overflow-y-auto shrink-0">
        <div className="px-6 py-5 border-b">
          <div className="font-bold text-indigo-700 text-lg">📚 BookStore</div>
          <div className="text-xs text-gray-500 mt-1">{panelLabel}</div>
        </div>
        <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-3 py-4 border-t">
          {user && (
            <div className="text-xs text-gray-500 px-3 mb-2">
              Logged in as <span className="font-medium text-gray-700">{user.full_name}</span>
            </div>
          )}
          <button
            onClick={onLogout}
            className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
          >
            Logout
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
