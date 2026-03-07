import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { getCustomerOrders, getOrder } from '../../api/orders'
import { useAuth } from '../../contexts/AuthContext'
import { Spinner, LoadingPage } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorPage } from '../../components/common/ErrorBanner'
import { Badge, ORDER_STATUS_COLOR, PAYMENT_STATUS_COLOR } from '../../components/common/Badge'
import { formatCurrency, formatDate } from '../../utils/format'

// Order list
function OrderList() {
  const { customer } = useAuth()
  const location = useLocation()
  const success = location.state?.success
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getCustomerOrders(customer.id)
      .then(setOrders)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [customer.id])

  if (loading) return <Spinner />
  if (error) return <ErrorPage message={error} />

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-gray-800">My Orders</h1>

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 rounded-xl px-5 py-4 text-sm">
          🎉 Your order has been placed successfully!
        </div>
      )}

      {orders.length === 0 ? (
        <div className="bg-white rounded-2xl border p-8">
          <EmptyState icon="📦" title="No orders yet" message="Place your first order to see it here." />
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {orders.map((order) => (
            <Link
              key={order.id}
              to={`/orders/${order.id}`}
              className="bg-white rounded-xl border hover:shadow-md transition-shadow p-5 flex flex-col sm:flex-row sm:items-center gap-4"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-gray-800">Order #{order.id}</span>
                  <Badge color={ORDER_STATUS_COLOR[order.status] || 'gray'}>{order.status}</Badge>
                </div>
                <p className="text-sm text-gray-500">{formatDate(order.created_at)}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {order.items?.length || 0} item(s) · {order.payment_method}
                </p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-indigo-700">{formatCurrency(order.total_amount)}</div>
                <div className="text-xs text-gray-400 mt-1">
                  <Badge color={PAYMENT_STATUS_COLOR[order.payment_status] || 'gray'}>
                    {order.payment_status}
                  </Badge>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

// Single order detail
function OrderDetail({ orderId }) {
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getOrder(orderId)
      .then(setOrder)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [orderId])

  if (loading) return <LoadingPage />
  if (error) return <ErrorPage message={error} />
  if (!order) return null

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Link to="/orders" className="text-sm text-indigo-600 hover:underline">← Orders</Link>
        <h1 className="text-xl font-bold text-gray-800">Order #{order.id}</h1>
        <Badge color={ORDER_STATUS_COLOR[order.status] || 'gray'}>{order.status}</Badge>
      </div>

      <div className="bg-white rounded-2xl border p-6 flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-400 text-xs mb-1">Date</p>
            <p className="font-medium">{formatDate(order.created_at)}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs mb-1">Payment</p>
            <div className="flex items-center gap-2">
              <span>{order.payment_method}</span>
              <Badge color={PAYMENT_STATUS_COLOR[order.payment_status] || 'gray'}>{order.payment_status}</Badge>
            </div>
          </div>
          <div>
            <p className="text-gray-400 text-xs mb-1">Shipping</p>
            <p className="font-medium">{order.shipping_method}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs mb-1">Address</p>
            <p className="font-medium text-xs">{order.shipping_address}</p>
          </div>
        </div>

        <div className="border-t pt-4">
          <h3 className="font-semibold text-gray-700 mb-3 text-sm">Items</h3>
          <div className="flex flex-col gap-2">
            {(order.items || []).map((item) => (
              <div key={item.id} className="flex justify-between text-sm">
                <span className="text-gray-700">{item.book_title_snapshot} × {item.quantity}</span>
                <span className="text-gray-800">{formatCurrency(item.subtotal)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t pt-4 flex justify-between font-bold text-gray-800">
          <span>Total</span>
          <span className="text-indigo-700">{formatCurrency(order.total_amount)}</span>
        </div>
      </div>
    </div>
  )
}

export default function OrderHistoryPage() {
  const { id } = useParams()
  return id ? <OrderDetail orderId={id} /> : <OrderList />
}
