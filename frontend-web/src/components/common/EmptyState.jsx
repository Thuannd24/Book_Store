export function EmptyState({ icon = '📭', title = 'Nothing here yet', message = '' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center text-gray-500">
      <span className="text-5xl mb-4">{icon}</span>
      <h3 className="text-lg font-semibold text-gray-700 mb-1">{title}</h3>
      {message && <p className="text-sm">{message}</p>}
    </div>
  )
}
