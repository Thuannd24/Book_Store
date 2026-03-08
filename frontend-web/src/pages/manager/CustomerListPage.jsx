import { useEffect, useState } from 'react'
import { getCustomerList } from '../../api/customers'
import { Spinner } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { formatDate } from '../../utils/format'

export default function CustomerListPage() {
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    getCustomerList()
      .then(setCustomers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const displayed = customers.filter((c) =>
    !search ||
    c.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    c.email?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Customers</h1>
          <p className="text-gray-500 text-sm">{customers.length} active customers</p>
        </div>
      </div>

      <div>
        <input
          type="search"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <Spinner />
      ) : displayed.length === 0 ? (
        <EmptyState icon="👥" title="No customers found" message="No customers match your search." />
      ) : (
        <div className="bg-white rounded-2xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Phone</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Address</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {displayed.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500 text-xs">#{c.id}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">{c.full_name || '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{c.email}</td>
                  <td className="px-4 py-3 text-gray-500">{c.phone || '—'}</td>
                  <td className="px-4 py-3 text-gray-500 max-w-[200px] truncate" title={c.address}>{c.address || '—'}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">{formatDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
