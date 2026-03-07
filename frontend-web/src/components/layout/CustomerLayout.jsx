import { Outlet } from 'react-router-dom'
import { CustomerNavbar } from './CustomerNavbar'

export function CustomerLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <CustomerNavbar />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Outlet />
      </main>
      <footer className="bg-white border-t mt-16 py-6 text-center text-xs text-gray-400">
        © 2026 BookStore — Academic Microservices Project
      </footer>
    </div>
  )
}
