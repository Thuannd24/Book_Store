import { useEffect, useState } from 'react'
import { getBooks } from '../../api/books'
import { getCustomerReviews, createReview } from '../../api/reviews'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../../components/common/Button'
import { Select, Textarea } from '../../components/common/Input'
import { StarRating } from '../../components/common/StarRating'
import { Spinner } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { formatDate } from '../../utils/format'

export default function ReviewPage() {
  const { customer } = useAuth()
  const [books, setBooks] = useState([])
  const [myReviews, setMyReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [form, setForm] = useState({ book_id: '', rating: 0, comment: '' })
  const [formErrors, setFormErrors] = useState({})

  useEffect(() => {
    Promise.all([getBooks(), getCustomerReviews(customer.id).catch(() => [])])
      .then(([bks, revs]) => {
        setBooks(bks)
        setMyReviews(Array.isArray(revs) ? revs : [])
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [customer.id])

  const validate = () => {
    const e = {}
    if (!form.book_id) e.book_id = 'Select a book'
    if (form.rating < 1) e.rating = 'Please give a rating'
    if (!form.comment.trim()) e.comment = 'Comment is required'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setFormErrors(errs); return }
    setSubmitting(true)
    setError('')
    setSuccess('')
    try {
      const review = await createReview({
        book_id: Number(form.book_id),
        customer_id: customer.id,
        rating: form.rating,
        comment: form.comment,
      })
      setMyReviews((r) => [review, ...r])
      setForm({ book_id: '', rating: 0, comment: '' })
      setSuccess('✅ Your review has been submitted!')
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-8">
      <h1 className="text-2xl font-bold text-gray-800">My Reviews</h1>

      {/* Submit form */}
      <div className="bg-white rounded-2xl border p-6 flex flex-col gap-5">
        <h2 className="font-semibold text-gray-700">Write a Review</h2>
        <ErrorBanner message={error} />
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Select
            label="Book"
            required
            value={form.book_id}
            onChange={(e) => setForm((f) => ({ ...f, book_id: e.target.value }))}
            error={formErrors.book_id}
          >
            <option value="">Select a book...</option>
            {books.map((b) => (
              <option key={b.id} value={b.id}>{b.title}</option>
            ))}
          </Select>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700">Rating <span className="text-red-500">*</span></label>
            <StarRating
              value={form.rating}
              onRate={(r) => setForm((f) => ({ ...f, rating: r }))}
            />
            {formErrors.rating && <p className="text-xs text-red-600">{formErrors.rating}</p>}
          </div>

          <Textarea
            label="Comment"
            required
            placeholder="Share your thoughts about this book..."
            value={form.comment}
            onChange={(e) => setForm((f) => ({ ...f, comment: e.target.value }))}
            error={formErrors.comment}
          />

          <Button type="submit" loading={submitting}>Submit Review</Button>
        </form>
      </div>

      {/* My reviews list */}
      <div>
        <h2 className="font-semibold text-gray-700 mb-4">My Previous Reviews</h2>
        {loading ? (
          <Spinner />
        ) : myReviews.length === 0 ? (
          <EmptyState icon="✍️" title="No reviews yet" message="Share your thoughts on books you've read." />
        ) : (
          <div className="flex flex-col gap-3">
            {myReviews.map((rev) => {
              const bookTitle = books.find((b) => b.id === rev.book_id)?.title
              return (
                <div key={rev.id} className="bg-white rounded-xl border p-4">
                  <div className="flex items-center gap-2 mb-1">
                    <StarRating value={rev.rating} readonly />
                    <span className="text-xs text-gray-400">{formatDate(rev.created_at)}</span>
                  </div>
                  <p className="text-xs text-indigo-600 mb-1">
                    {bookTitle ?? `Book #${rev.book_id}`}
                  </p>
                  <p className="text-sm text-gray-700">{rev.comment}</p>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
