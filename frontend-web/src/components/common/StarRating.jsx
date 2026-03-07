export function StarRating({ value = 0, max = 5, onRate, readonly = false }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: max }, (_, i) => i + 1).map((star) => (
        <button
          key={star}
          type="button"
          disabled={readonly}
          onClick={() => onRate && onRate(star)}
          className={`
            text-xl leading-none transition-colors
            ${readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110'}
            ${star <= value ? 'text-yellow-400' : 'text-gray-300'}
          `}
        >
          ★
        </button>
      ))}
    </div>
  )
}
