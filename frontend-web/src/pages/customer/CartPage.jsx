import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCart, updateCartItem, removeCartItem } from '../../api/cart'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../../components/common/Button'
import { Spinner } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { formatCurrency } from '../../utils/format'

export default function CartPage() {
  const { customer } = useAuth()
  const navigate = useNavigate()
  const [cart, setCart] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updating, setUpdating] = useState(null)

  const fetchCart = () => {
    setLoading(true)
    getCart(customer.id)
      .then(setCart)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchCart() }, [customer.id])

  const handleQtyChange = async (itemId, qty) => {
    if (qty < 1) return
    setUpdating(itemId)
    try {
      const updated = await updateCartItem(itemId, { quantity: qty })
      setCart(updated)
    } catch (e) {
      setError(e.message)
    } finally {
      setUpdating(null)
    }
  }

  const handleRemove = async (itemId) => {
    setUpdating(itemId)
    try {
      const updated = await removeCartItem(itemId)
      setCart(updated)
    } catch (e) {
      setError(e.message)
    } finally {
      setUpdating(null)
    }
  }

  const items = cart?.items || []

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-gray-800">🛒 Shopping Cart</h1>

      <ErrorBanner message={error} />

      {loading ? (
        <Spinner />
      ) : items.length === 0 ? (
        <div className="bg-white rounded-2xl border p-8">
          <EmptyState icon="🛒" title="Your cart is empty" message="Browse our books and add some to cart." />
          <div className="flex justify-center mt-4">
            <Button variant="outline" onClick={() => navigate('/books')}>Browse Books</Button>
          </div>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-2xl border divide-y">
            {items.map((item) => (
              <div key={item.id} className="flex items-center gap-4 px-6 py-4">
                <div className="w-12 h-16 bg-indigo-50 rounded-lg flex items-center justify-center shrink-0">
                  <span className="text-2xl">📖</span>
                </div>

                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-800 truncate">{item.book_title_snapshot}</p>
                  <p className="text-xs text-gray-400">{formatCurrency(item.price_snapshot)} each</p>
                </div>

                {/* Quantity */}
                <div className="flex items-center gap-2 border rounded-lg px-2 py-1">
                  <button
                    disabled={updating === item.id}
                    onClick={() => handleQtyChange(item.id, item.quantity - 1)}
                    className="text-gray-500 hover:text-gray-800 disabled:opacity-40 font-bold"
                  >−</button>
                  <span className="w-5 text-center text-sm">{item.quantity}</span>
                  <button
                    disabled={updating === item.id}
                    onClick={() => handleQtyChange(item.id, item.quantity + 1)}
                    className="text-gray-500 hover:text-gray-800 disabled:opacity-40 font-bold"
                  >+</button>
                </div>

                <p className="text-sm font-semibold text-indigo-700 w-24 text-right">
                  {formatCurrency(item.subtotal)}
                </p>

                <button
                  onClick={() => handleRemove(item.id)}
                  disabled={updating === item.id}
                  className="text-red-400 hover:text-red-600 disabled:opacity-40 ml-2"
                >✕</button>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="bg-white rounded-2xl border p-6 flex flex-col gap-4">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Items ({cart.total_items})</span>
              <span>{formatCurrency(cart.total_amount)}</span>
            </div>
            <div className="border-t pt-4 flex justify-between font-bold text-gray-800 text-lg">
              <span>Total</span>
              <span className="text-indigo-700">{formatCurrency(cart.total_amount)}</span>
            </div>
            <Button size="lg" onClick={() => navigate('/checkout')}>
              Proceed to Checkout →
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
