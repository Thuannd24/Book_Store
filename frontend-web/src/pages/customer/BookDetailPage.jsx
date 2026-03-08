import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getBook } from '../../api/books'
import { getBookRating, getBookReviews } from '../../api/reviews'
import { addToCart } from '../../api/cart'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../../components/common/Button'
import { StarRating } from '../../components/common/StarRating'
import { Badge } from '../../components/common/Badge'
import { Spinner, LoadingPage } from '../../components/common/Spinner'
import { ErrorPage } from '../../components/common/ErrorBanner'
import { EmptyState } from '../../components/common/EmptyState'
import { ToastContainer, useToast } from '../../components/common/Toast'
import { formatCurrency, formatDate } from '../../utils/format'

export default function BookDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { customer } = useAuth()

  const [book, setBook] = useState(null)
  const [rating, setRating] = useState(null)
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cartLoading, setCartLoading] = useState(false)
  const [qty, setQty] = useState(1)
  const { toasts, dismiss, toast } = useToast()

  useEffect(() => {
    setLoading(true)
    Promise.all([
      getBook(id),
      getBookRating(id).catch(() => null),
      getBookReviews(id).catch(() => []),
    ])
      .then(([b, r, revs]) => {
        setBook(b)
        setRating(r)
        setReviews(Array.isArray(revs) ? revs : [])
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  const handleAddToCart = async () => {
    if (!customer) { navigate('/login', { state: { from: `/books/${id}` } }); return }
    setCartLoading(true)
    try {
      await addToCart(customer.id, { book_id: Number(id), quantity: qty })
      toast.success('Added to cart! 🛒')
    } catch (e) {
      toast.error(e.message)
    } finally {
      setCartLoading(false)
    }
  }

  if (loading) return <LoadingPage />
  if (error) return <ErrorPage message={error} />
  if (!book) return null

  return (
    <div className="flex flex-col gap-10">
      {/* Book detail */}
      <div className="bg-white rounded-2xl shadow-sm border p-6 md:p-8 grid md:grid-cols-3 gap-8">
        {/* Cover */}
        <div className="md:col-span-1">
          <div className="aspect-[3/4] bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-xl flex items-center justify-center overflow-hidden">
            {book.image_url ? (
              <img src={book.image_url} alt={book.title} className="w-full h-full object-cover" />
            ) : (
              <span className="text-8xl">📖</span>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="md:col-span-2 flex flex-col gap-4">
          <div>
            <Badge color="indigo">{book.category_name_snapshot || 'Uncategorized'}</Badge>
            <h1 className="text-2xl font-bold text-gray-900 mt-2">{book.title}</h1>
            <p className="text-gray-500 text-sm mt-1">by {book.author}</p>
            {book.publisher && <p className="text-gray-400 text-xs mt-1">Publisher: {book.publisher}</p>}
          </div>

          {rating && (
            <div className="flex items-center gap-2">
              <StarRating value={Math.round(rating.average_rating || 0)} readonly />
              <span className="text-sm text-gray-600">
                {Number(rating.average_rating || 0).toFixed(1)} ({rating.review_count} reviews)
              </span>
            </div>
          )}

          <div className="text-3xl font-bold text-indigo-700">{formatCurrency(book.price)}</div>

          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium px-3 py-1 rounded-full ${book.stock > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              {book.stock > 0 ? `In Stock (${book.stock})` : 'Out of Stock'}
            </span>
          </div>

          {book.description && (
            <p className="text-gray-600 text-sm leading-relaxed">{book.description}</p>
          )}

          {/* Cart action */}
          <div className="flex items-center gap-3 mt-2">
            <div className="flex items-center gap-2 border rounded-lg px-3 py-1.5">
              <button onClick={() => setQty((q) => Math.max(1, q - 1))} className="text-gray-500 hover:text-gray-800 font-bold">−</button>
              <span className="w-6 text-center text-sm font-medium">{qty}</span>
              <button onClick={() => setQty((q) => Math.min(book.stock, q + 1))} className="text-gray-500 hover:text-gray-800 font-bold">+</button>
            </div>
            <Button
              onClick={handleAddToCart}
              loading={cartLoading}
              disabled={book.stock === 0}
              size="lg"
            >
              🛒 Add to Cart
            </Button>
          </div>

          <div className="text-xs text-gray-400 pt-2 border-t">
            ISBN: {book.isbn || '—'} · Added: {formatDate(book.created_at)}
          </div>
        </div>
      </div>

      {/* Reviews */}
      <div>
        <h2 className="text-xl font-bold text-gray-800 mb-4">Customer Reviews</h2>
        {reviews.length === 0 ? (
          <EmptyState icon="💬" title="No reviews yet" message="Be the first to review this book." />
        ) : (
          <div className="flex flex-col gap-4">
            {reviews.map((rev) => (
              <div key={rev.id} className="bg-white rounded-xl border p-4">
                <div className="flex items-center gap-2 mb-1">
                  <StarRating value={rev.rating} readonly />
                  <span className="text-xs text-gray-400">{formatDate(rev.created_at)}</span>
                </div>
                <p className="text-sm text-gray-700">{rev.comment}</p>
                <p className="text-xs text-gray-400 mt-1">Verified Buyer</p>
              </div>
            ))}
          </div>
        )}

        {customer && (
          <div className="mt-4">
            <Button variant="outline" onClick={() => navigate('/reviews')}>
              Write a Review
            </Button>
          </div>
        )}
      </div>

      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </div>
  )
}
