import { useState } from 'react'

export function StarRating({ value = 0, max = 5, onRate, readonly = false }) {
  const [hovered, setHovered] = useState(0)

  const active = readonly ? value : (hovered || value)

  return (
    <div
      className="flex gap-0.5"
      onMouseLeave={() => !readonly && setHovered(0)}
    >
      {Array.from({ length: max }, (_, i) => i + 1).map((star) => (
        <button
          key={star}
          type="button"
          disabled={readonly}
          onClick={() => !readonly && onRate && onRate(star)}
          onMouseEnter={() => !readonly && setHovered(star)}
          className={`
            text-xl leading-none transition-all duration-100
            ${readonly ? 'cursor-default' : 'cursor-pointer hover:scale-125'}
            ${star <= active ? 'text-yellow-400' : 'text-gray-200'}
          `}
        >
          ★
        </button>
      ))}
    </div>
  )
}
