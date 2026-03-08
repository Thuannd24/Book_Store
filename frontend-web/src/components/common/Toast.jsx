import { useEffect, useRef, useState } from 'react'

function ToastItem({ id, type, message, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(() => onDismiss(id), 3500)
    return () => clearTimeout(t)
  }, [id, onDismiss])

  const colors = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    info: 'bg-indigo-600',
  }
  const icons = { success: '✅', error: '❌', info: 'ℹ️' }

  return (
    <div
      className={`flex items-center gap-3 ${colors[type]} text-white px-4 py-3 rounded-xl shadow-lg text-sm max-w-xs w-full
        transition-opacity duration-300 opacity-100`}
    >
      <span>{icons[type]}</span>
      <span className="flex-1">{message}</span>
      <button onClick={() => onDismiss(id)} className="text-white/70 hover:text-white ml-1">✕</button>
    </div>
  )
}

export function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 items-end">
      {toasts.map((t) => (
        <ToastItem key={t.id} {...t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

export function useToast() {
  const [toasts, setToasts] = useState([])
  const idRef = useRef(0)

  const dismiss = (id) => setToasts((prev) => prev.filter((t) => t.id !== id))

  const toast = {
    success: (message) => setToasts((prev) => [...prev, { id: ++idRef.current, type: 'success', message }]),
    error: (message) => setToasts((prev) => [...prev, { id: ++idRef.current, type: 'error', message }]),
    info: (message) => setToasts((prev) => [...prev, { id: ++idRef.current, type: 'info', message }]),
  }

  return { toasts, dismiss, toast }
}
