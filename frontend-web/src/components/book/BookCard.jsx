import { Link } from 'react-router-dom'
import { formatCurrency } from '../../utils/format'
import { StarRating } from '../common/StarRating'

export function BookCard({ book, rating }) {
  return (
    <Link
      to={`/books/${book.id}`}
      className="group bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow overflow-hidden flex flex-col"
    >
      <div className="aspect-[3/4] bg-gradient-to-br from-indigo-50 to-indigo-100 flex items-center justify-center overflow-hidden">
        {book.image_url ? (
          <img
            src={book.image_url}
            alt={book.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <span className="text-5xl">📖</span>
        )}
      </div>
      <div className="p-3 flex flex-col gap-1 flex-1">
        <span className="text-xs text-indigo-600 font-medium truncate">
          {book.category_name_snapshot || 'Uncategorized'}
        </span>
        <h3 className="text-sm font-semibold text-gray-800 line-clamp-2 leading-snug">
          {book.title}
        </h3>
        <p className="text-xs text-gray-500 truncate">{book.author}</p>
        {rating !== undefined && (
          <StarRating value={Math.round(rating)} readonly />
        )}
        <div className="mt-auto pt-2 flex items-center justify-between">
          <span className="text-indigo-700 font-bold text-sm">
            {formatCurrency(book.price)}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              book.stock > 0
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {book.stock > 0 ? `${book.stock} left` : 'Out of stock'}
          </span>
        </div>
      </div>
    </Link>
  )
}
