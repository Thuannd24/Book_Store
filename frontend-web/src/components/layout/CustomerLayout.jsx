import { Outlet } from 'react-router-dom'
import { CustomerNavbar } from './CustomerNavbar'

export function CustomerLayout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <CustomerNavbar />
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        <Outlet />
      </main>
      <footer className="bg-white border-t mt-auto py-6 text-center text-xs text-gray-400">
        © 2026 BookStore
      </footer>
    </div>
  )
}
