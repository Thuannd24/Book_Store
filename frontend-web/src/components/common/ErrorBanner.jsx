export function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm">
      ⚠️ {message}
    </div>
  )
}

export function ErrorPage({ message = 'Something went wrong.' }) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center gap-3 text-red-600">
      <span className="text-5xl">❌</span>
      <h3 className="text-lg font-semibold">Error</h3>
      <p className="text-sm text-gray-600 max-w-xs">{message}</p>
    </div>
  )
}
