import { useEffect, useState } from 'react'
import { getAllOrders, updateOrderStatus } from '../../api/orders'
import { Spinner } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { Badge } from '../../components/common/Badge'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { formatCurrency, formatDate } from '../../utils/format'

const STATUS_COLOR = {
  PENDING: 'gray',
  CREATED: 'gray',
  PAYMENT_CREATED: 'yellow',
  PAYMENT_RESERVED: 'yellow',
  SHIPMENT_CREATED: 'blue',
  SHIPMENT_RESERVED: 'blue',
  CONFIRMED: 'green',
  SHIPPING: 'indigo',
  DELIVERED: 'green',
  FAILED: 'red',
  COMPENSATING: 'red',
  COMPENSATED: 'red',
}

const NEXT_STATUS = {
  CONFIRMED: { label: 'Mark as Shipping', next: 'SHIPPING' },
  SHIPPING: { label: 'Mark as Delivered', next: 'DELIVERED' },
}

const STATUS_FILTER_OPTIONS = [
  { value: '', label: 'All Orders' },
  { value: 'CONFIRMED', label: 'Confirmed' },
  { value: 'SHIPPING', label: 'Shipping' },
  { value: 'DELIVERED', label: 'Delivered' },
  { value: 'FAILED', label: 'Failed' },
  { value: 'COMPENSATED', label: 'Compensated' },
]

export default function OrderManagementPage() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [confirmTarget, setConfirmTarget] = useState(null) // { order, next, label }

  useEffect(() => {
    setLoading(true)
    getAllOrders()
      .then(setOrders)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handleStatusClick = (order) => {
    const action = NEXT_STATUS[order.status]
    if (!action) return
    setConfirmTarget({ order, ...action })
  }

  const handleConfirmUpdate = async () => {
    if (!confirmTarget) return
    try {
      const updated = await updateOrderStatus(confirmTarget.order.id, confirmTarget.next)
      setOrders((prev) => prev.map((o) => (o.id === updated.id ? updated : o)))
    } catch (e) {
      setError(e.message)
    }
  }

  const displayed = orders.filter((o) => {
    const matchStatus = !statusFilter || o.status === statusFilter
    const matchSearch =
      !search ||
      String(o.id).includes(search) ||
      String(o.customer_id).includes(search) ||
      o.shipping_address?.toLowerCase().includes(search.toLowerCase())
    return matchStatus && matchSearch
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Order Management</h1>
          <p className="text-gray-500 text-sm">{orders.length} orders total</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <input
          type="search"
          placeholder="Search by Order ID, Customer ID, address..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        >
          {STATUS_FILTER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <Spinner />
      ) : displayed.length === 0 ? (
        <EmptyState icon="📦" title="No orders found" message="No orders match your current filters." />
      ) : (
        <div className="bg-white rounded-2xl border overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Order</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Customer ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Items</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Address</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Method</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Total</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Shipping</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Date</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {displayed.map((order) => {
                const action = NEXT_STATUS[order.status]
                return (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-semibold text-gray-800">#{order.id}</td>
                    <td className="px-4 py-3 text-gray-600">{order.customer_id}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-0.5">
                        {order.items?.map((item) => (
                          <span key={item.id} className="text-xs text-gray-600">
                            {item.book_title_snapshot} × {item.quantity}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600 max-w-[160px] truncate" title={order.shipping_address}>
                      {order.shipping_address}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      <div>{order.payment_method}</div>
                      <div>{order.shipping_method}</div>
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-800">
                      {formatCurrency(order.total_amount)}
                    </td>
                    <td className="px-4 py-3">
                      <Badge color={STATUS_COLOR[order.status] || 'gray'}>{order.status}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {order.shipping_status && (
                        <Badge color={STATUS_COLOR[order.shipping_status] || 'gray'}>
                          {order.shipping_status}
                        </Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                      {formatDate(order.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {action && (
                        <button
                          onClick={() => handleStatusClick(order)}
                          className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap"
                        >
                          {action.label}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        isOpen={!!confirmTarget}
        onClose={() => setConfirmTarget(null)}
        onConfirm={handleConfirmUpdate}
        title={`Update Order #${confirmTarget?.order?.id}?`}
        message={`Are you sure you want to mark Order #${confirmTarget?.order?.id} as "${confirmTarget?.next}"?`}
        confirmLabel={confirmTarget?.label || 'Confirm'}
      />
    </div>
  )
}
