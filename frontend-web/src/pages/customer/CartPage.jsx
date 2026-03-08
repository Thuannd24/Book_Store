import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCart, updateCartItem, removeCartItem } from '../../api/cart'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../../components/common/Button'
import { Spinner } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { ToastContainer, useToast } from '../../components/common/Toast'
import { formatCurrency } from '../../utils/format'

export default function CartPage() {
  const { customer } = useAuth()
  const navigate = useNavigate()
  const [cart, setCart] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updating, setUpdating] = useState(null)
  const [confirmRemove, setConfirmRemove] = useState(null)
  const { toasts, dismiss, toast } = useToast()

  const fetchCart = useCallback(() => {
    setLoading(true)
    getCart(customer.id)
      .then(setCart)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [customer.id])

  useEffect(() => { fetchCart() }, [fetchCart])

  const handleQtyChange = async (itemId, qty) => {
    if (qty < 1) return
    setUpdating(itemId)
    try {
      const updated = await updateCartItem(itemId, { quantity: qty })
      setCart(updated)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setUpdating(null)
    }
  }

  const handleRemoveConfirmed = async () => {
    if (!confirmRemove) return
    const itemId = confirmRemove.id
    setUpdating(itemId)
    try {
      const updated = await removeCartItem(itemId)
      setCart(updated)
      toast.success(`"${confirmRemove.book_title_snapshot}" removed from cart.`)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setUpdating(null)
      setConfirmRemove(null)
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
              <div key={item.id} className="flex items-center gap-4 px-6 py-4 transition-opacity duration-150"
                style={{ opacity: updating === item.id ? 0.5 : 1 }}>
                <div className="w-12 h-16 bg-indigo-50 rounded-lg flex items-center justify-center shrink-0">
                  <span className="text-2xl">📖</span>
                </div>

                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-800 truncate">{item.book_title_snapshot}</p>
                  <p className="text-xs text-gray-400">{formatCurrency(item.price_snapshot)} each</p>
                </div>

                {/* Quantity stepper */}
                <div className="flex items-center gap-1 border rounded-lg">
                  <button
                    disabled={updating === item.id || item.quantity <= 1}
                    onClick={() => handleQtyChange(item.id, item.quantity - 1)}
                    className="px-3 py-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-50 disabled:opacity-40 rounded-l-lg transition-colors font-bold"
                  >−</button>
                  <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
                  <button
                    disabled={updating === item.id}
                    onClick={() => handleQtyChange(item.id, item.quantity + 1)}
                    className="px-3 py-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-50 disabled:opacity-40 rounded-r-lg transition-colors font-bold"
                  >+</button>
                </div>

                <p className="text-sm font-semibold text-indigo-700 w-24 text-right">
                  {formatCurrency(item.subtotal)}
                </p>

                <button
                  onClick={() => setConfirmRemove(item)}
                  disabled={updating === item.id}
                  title="Remove item"
                  className="text-red-300 hover:text-red-500 hover:bg-red-50 disabled:opacity-40 ml-2 p-1.5 rounded-lg transition-colors"
                >🗑️</button>
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

      {/* Confirm remove dialog */}
      <ConfirmDialog
        isOpen={!!confirmRemove}
        onClose={() => setConfirmRemove(null)}
        onConfirm={handleRemoveConfirmed}
        title="Remove item?"
        message={`Remove "${confirmRemove?.book_title_snapshot}" from your cart?`}
        confirmLabel="Remove"
        danger
      />

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </div>
  )
}
