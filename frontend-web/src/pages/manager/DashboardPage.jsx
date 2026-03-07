import { useEffect, useState } from 'react'
import { getDashboardSummary } from '../../api/managers'
import { Spinner } from '../../components/common/Spinner'
import { ErrorPage } from '../../components/common/ErrorBanner'
import { Badge, ORDER_STATUS_COLOR } from '../../components/common/Badge'
import { formatCurrency, formatDate } from '../../utils/format'

function StatCard({ label, value, sub, icon, color = 'indigo' }) {
  const colors = {
    indigo: 'bg-indigo-50 text-indigo-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
  }
  return (
    <div className="bg-white rounded-2xl border p-5 flex items-start gap-4">
      <div className={`${colors[color]} rounded-xl p-3 text-2xl`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-gray-800">{value ?? '—'}</p>
        <p className="text-sm font-medium text-gray-600">{label}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getDashboardSummary()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />
  if (error) return <ErrorPage message={error} />

  // Normalise - backend returns {total_customers, total_books, total_orders, total_reviews, notes?}
  const totalCustomers = data?.total_customers ?? '—'
  const totalOrders = data?.total_orders ?? '—'
  const totalBooks = data?.total_books ?? '—'
  const totalReviews = data?.total_reviews ?? '—'
  const recentOrders = data?.recent_orders ?? []
  const notes = data?.notes ?? {}

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Overview of your bookstore's performance</p>
      </div>

      {/* Stats grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon="👥" label="Total Customers" value={totalCustomers} color="blue"
          sub={notes.total_customers ? `⚠ ${notes.total_customers}` : null} />
        <StatCard icon="📚" label="Total Books" value={totalBooks} color="purple"
          sub={notes.total_books ? `⚠ ${notes.total_books}` : null} />
        <StatCard icon="📦" label="Total Orders" value={totalOrders} color="green"
          sub={notes.total_orders ? `⚠ ${notes.total_orders}` : null} />
        <StatCard icon="⭐" label="Total Reviews" value={totalReviews} color="yellow"
          sub={notes.total_reviews ? `⚠ ${notes.total_reviews}` : null} />
      </div>

      {/* Recent orders */}
      {recentOrders.length > 0 ? (
        <div className="bg-white rounded-2xl border">
          <div className="px-6 py-4 border-b">
            <h2 className="font-semibold text-gray-800">Recent Orders</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Order ID</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Customer</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">Amount</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {recentOrders.map((order) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800">#{order.id}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {order.customer_name ?? `Customer #${order.customer_id}`}
                    </td>
                    <td className="px-4 py-3">
                      <Badge color={ORDER_STATUS_COLOR[order.status] || 'gray'}>{order.status}</Badge>
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-800">
                      {formatCurrency(order.total_amount)}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{formatDate(order.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border p-8 text-center text-gray-500 text-sm">
          No recent order data available from the dashboard API.
        </div>
      )}
    </div>
  )
}
