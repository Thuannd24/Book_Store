import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRecommendations } from '../../api/recommendations'
import { getBookById } from '../../api/books'
import { useAuth } from '../../contexts/AuthContext'
import { BookCard } from '../../components/book/BookCard'
import { Spinner } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorPage } from '../../components/common/ErrorBanner'

export default function RecommendationPage() {
  const { customer } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getRecommendations(customer.id)
        const items = result?.recommendations || []
        const enriched = await Promise.all(
          items.map((item) =>
            getBookById(item.book_id)
              .then((fullBook) => ({
                ...fullBook,
                average_rating: item.average_rating,
                reason: item.reason,
                score: item.score,
              }))
              .catch((err) => {
                console.error('Failed to fetch book', item.book_id, err)
                return null
              })
          )
        )
        setData({ ...result, recommendations: enriched.filter(Boolean) })
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [customer.id])

  if (loading) return <Spinner />
  if (error) return <ErrorPage message={error} />

  const recs = data?.recommendations || []

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Recommended For You ✨</h1>
        <p className="text-gray-500 text-sm mt-1">
          Based on your purchase history and reviews, {customer.full_name}.
        </p>
      </div>

      {recs.length === 0 ? (
        <div className="bg-white rounded-2xl border p-8">
          <EmptyState
            icon="🤖"
            title="Not enough data yet"
            message="Place some orders and write reviews to get personalised recommendations."
          />
          <div className="flex justify-center mt-4">
            <Link
              to="/books"
              className="bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
            >
              Browse Books
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {recs.map((book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>
      )}
    </div>
  )
}
