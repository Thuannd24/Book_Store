import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getBooks } from '../../api/books'
import { getCategories } from '../../api/catalog'
import { BookCard } from '../../components/book/BookCard'
import { Spinner } from '../../components/common/Spinner'
import { ErrorBanner } from '../../components/common/ErrorBanner'

export default function HomePage() {
  const [featured, setFeatured] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getBooks(), getCategories()])
      .then(([books, cats]) => {
        setFeatured(books.slice(0, 8))
        setCategories(cats.slice(0, 6))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="flex flex-col gap-12">
      {/* Hero */}
      <section className="rounded-2xl bg-gradient-to-br from-indigo-600 to-indigo-800 text-white px-8 py-16 flex flex-col items-center text-center gap-6">
        <h1 className="text-4xl md:text-5xl font-extrabold leading-tight">
          Discover Your Next<br />Favourite Book
        </h1>
        <p className="text-indigo-200 text-lg max-w-xl">
          Thousands of titles across every genre — delivered fast, priced right.
        </p>
        <Link
          to="/books"
          className="bg-white text-indigo-700 font-semibold px-8 py-3 rounded-full hover:bg-indigo-50 transition"
        >
          Browse Books →
        </Link>
      </section>

      {/* Categories */}
      {categories.length > 0 && (
        <section>
          <h2 className="text-xl font-bold text-gray-800 mb-4">Browse by Category</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {categories.map((cat) => (
              <Link
                key={cat.id}
                to={`/books?category_id=${cat.id}`}
                className="bg-white rounded-xl border border-gray-100 shadow-sm px-4 py-5 flex flex-col items-center gap-2 hover:shadow-md hover:border-indigo-200 transition text-center"
              >
                <span className="text-2xl">🏷️</span>
                <span className="text-sm font-medium text-gray-700 truncate w-full text-center">
                  {cat.name}
                </span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Featured books */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">Featured Books</h2>
          <Link to="/books" className="text-sm text-indigo-600 hover:underline">
            View all →
          </Link>
        </div>
        <ErrorBanner message={error} />
        {loading ? (
          <Spinner />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {featured.map((book) => (
              <BookCard key={book.id} book={book} />
            ))}
          </div>
        )}
      </section>

      {/* CTA */}
      <section className="bg-indigo-50 rounded-2xl px-8 py-10 text-center">
        <h2 className="text-2xl font-bold text-indigo-800 mb-2">Personalised For You</h2>
        <p className="text-gray-600 mb-5">
          Login to see AI-powered book recommendations based on your purchase history.
        </p>
        <Link
          to="/login"
          className="bg-indigo-600 text-white px-6 py-2.5 rounded-full font-medium hover:bg-indigo-700 transition"
        >
          Get Started
        </Link>
      </section>
    </div>
  )
}
