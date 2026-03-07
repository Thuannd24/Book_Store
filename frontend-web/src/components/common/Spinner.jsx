export function Spinner({ size = 'md' }) {
  const sizes = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' }
  return (
    <div className="flex justify-center items-center py-8">
      <div
        className={`${sizes[size]} animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600`}
      />
    </div>
  )
}

export function LoadingPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <Spinner size="lg" />
    </div>
  )
}
