import { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getBooks } from '../../api/books'
import { getCategories } from '../../api/catalog'
import { BookCard } from '../../components/book/BookCard'
import { Spinner } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'

export default function BookListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [books, setBooks] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const categoryId = searchParams.get('category_id') || ''
  const [inputValue, setInputValue] = useState(searchParams.get('keyword') || '')
  const [debouncedKeyword, setDebouncedKeyword] = useState(searchParams.get('keyword') || '')

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedKeyword(inputValue)
    }, 400)
    return () => clearTimeout(timer)
  }, [inputValue])

  useEffect(() => {
    setSearchParams((p) => {
      const newP = new URLSearchParams(p)
      if (debouncedKeyword) newP.set('keyword', debouncedKeyword)
      else newP.delete('keyword')
      return newP
    })
  }, [debouncedKeyword, setSearchParams])

  const fetchBooks = useCallback(() => {
    setLoading(true)
    setError('')
    const params = {}
    if (debouncedKeyword) params.keyword = debouncedKeyword
    if (categoryId) params.category_id = categoryId
    getBooks(params)
      .then(setBooks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [debouncedKeyword, categoryId])

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    fetchBooks()
  }, [fetchBooks])

  const selectedCat = categories.find((c) => String(c.id) === categoryId)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-800">
            {selectedCat ? selectedCat.name : 'All Books'}
          </h1>
          <p className="text-gray-500 text-sm">{books.length} results</p>
        </div>

        {/* Search */}
        <div className="sm:w-72">
          <input
            type="search"
            placeholder="Search books or authors..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>
      </div>

      <div className="flex gap-6">
        {/* Sidebar categories — desktop */}
        <aside className="hidden md:flex flex-col gap-1 w-44 shrink-0 sticky top-24 self-start">
          <button
            onClick={() => { const p = new URLSearchParams(searchParams); p.delete('category_id'); setSearchParams(p) }}
            className={`text-left text-sm px-3 py-2 rounded-lg ${!categoryId ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            All Categories
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => { const p = new URLSearchParams(searchParams); p.set('category_id', cat.id); setSearchParams(p) }}
              className={`text-left text-sm px-3 py-2 rounded-lg truncate ${String(cat.id) === categoryId ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              {cat.name}
            </button>
          ))}
        </aside>

        {/* Book grid */}
        <div className="flex-1 min-w-0">
          {/* Mobile category select */}
          {categories.length > 0 && (
            <div className="md:hidden mb-4">
              <select
                value={categoryId}
                onChange={(e) => {
                  const p = new URLSearchParams(searchParams)
                  if (e.target.value) p.set('category_id', e.target.value)
                  else p.delete('category_id')
                  setSearchParams(p)
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>
          )}
          <ErrorBanner message={error} />
          {loading ? (
            <Spinner />
          ) : books.length === 0 ? (
            <EmptyState icon="📖" title="No books found" message="Try adjusting your search or category filter." />
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {books.map((book) => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
