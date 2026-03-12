import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCart } from '../../api/cart'
import { createOrder, getCustomerPromos } from '../../api/orders'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../../components/common/Button'
import { Input, Select } from '../../components/common/Input'
import { Spinner } from '../../components/common/Spinner'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { formatCurrency } from '../../utils/format'

export default function CheckoutPage() {
  const { customer } = useAuth()
  const navigate = useNavigate()
  const [cart, setCart] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    shipping_address: customer?.address || '',
    payment_method: 'COD',
    shipping_method: 'STANDARD',
    promo_code: '',
  })
  const [errors, setErrors] = useState({})
  const [promos, setPromos] = useState([])

  useEffect(() => {
    getCart(customer.id)
      .then(setCart)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))

    getCustomerPromos(customer.id)
      .then(setPromos)
      .catch(() => {})
  }, [customer.id])

  const shippingFee = form.shipping_method === 'EXPRESS' ? 50000 : 20000

  const validate = () => {
    const e = {}
    if (!form.shipping_address.trim()) e.shipping_address = 'Shipping address is required'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    if (!cart?.items?.length) { setError('Your cart is empty'); return }

    setSubmitting(true)
    setError('')
    try {
      const order = await createOrder({
        customer_id: customer.id,
        ...form,
        shipping_fee: String(shippingFee),
      })
      navigate(`/orders/${order.id}`, { state: { success: true } })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const field = (name) => ({
    value: form[name],
    onChange: (e) => { setForm((f) => ({ ...f, [name]: e.target.value })); setErrors((er) => ({ ...er, [name]: '' })) },
    error: errors[name],
  })

  const items = cart?.items || []
  const subtotal = parseFloat(cart?.total_amount || 0)
  const total = subtotal + shippingFee

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Checkout</h1>

      <ErrorBanner message={error} />

      {loading ? (
        <Spinner />
      ) : (
        <form onSubmit={handleSubmit} className="grid md:grid-cols-5 gap-8">
          {/* Left: form */}
          <div className="md:col-span-3 flex flex-col gap-6">
            <div className="bg-white rounded-2xl border p-6 flex flex-col gap-5">
              <h2 className="font-semibold text-gray-700">Shipping Details</h2>
              <Input
                label="Shipping Address"
                required
                placeholder="Enter delivery address"
                {...field('shipping_address')}
              />
              <Select label="Shipping Method" required {...field('shipping_method')}>
                <option value="STANDARD">Standard Delivery — {formatCurrency(20000)}</option>
                <option value="EXPRESS">Express Delivery — {formatCurrency(50000)}</option>
              </Select>
            </div>

            <div className="bg-white rounded-2xl border p-6 flex flex-col gap-5">
              <h2 className="font-semibold text-gray-700">Payment Method</h2>
              <Select label="Payment" required {...field('payment_method')}>
                <option value="COD">Cash on Delivery (COD)</option>
                <option value="BANK_TRANSFER">Bank Transfer</option>
              </Select>
              {form.payment_method === 'BANK_TRANSFER' && (
                <p className="text-xs text-green-700 bg-green-50 rounded-lg px-3 py-2">
                  ✅ Bank transfer orders are automatically confirmed.
                </p>
              )}
              {form.payment_method === 'COD' && (
                <p className="text-xs text-yellow-700 bg-yellow-50 rounded-lg px-3 py-2">
                  🏠 Pay when your order arrives.
                </p>
              )}
            </div>

            <div className="bg-white rounded-2xl border p-6 flex flex-col gap-4">
              <h2 className="font-semibold text-gray-700">Promo Code</h2>
              <Select
                label="Enter promo code"
                {...field('promo_code')}
              >
                <option value="">No promo code</option>
                {promos.map((p) => (
                  <option key={p.code} value={p.code}>
                    {p.code} — {p.percentage}% (tối đa {formatCurrency(p.max_discount_amount)})
                  </option>
                ))}
              </Select>
            </div>
          </div>

          {/* Right: order summary */}
          <div className="md:col-span-2 flex flex-col gap-4">
            <div className="bg-white rounded-2xl border p-6 flex flex-col gap-4">
              <h2 className="font-semibold text-gray-700">Order Summary</h2>

              <div className="divide-y max-h-64 overflow-auto">
                {items.map((item) => (
                  <div key={item.id} className="flex justify-between text-sm py-2 gap-2">
                    <span className="text-gray-700 truncate">{item.book_title_snapshot} × {item.quantity}</span>
                    <span className="text-gray-800 shrink-0">{formatCurrency(item.subtotal)}</span>
                  </div>
                ))}
              </div>

              <div className="border-t pt-3 flex flex-col gap-2 text-sm">
                <div className="flex justify-between text-gray-600">
                  <span>Subtotal</span>
                  <span>{formatCurrency(subtotal)}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Shipping</span>
                  <span>{formatCurrency(shippingFee)}</span>
                </div>
                <div className="flex justify-between font-bold text-gray-800 text-base border-t pt-2 mt-1">
                  <span>Total</span>
                  <span className="text-indigo-700">{formatCurrency(total)}</span>
                </div>
              </div>

              <Button type="submit" loading={submitting} size="lg" className="w-full mt-2">
                Place Order
              </Button>
            </div>
          </div>
        </form>
      )}
    </div>
  )
}
