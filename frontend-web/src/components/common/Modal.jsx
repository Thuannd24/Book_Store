import { useEffect, useState } from 'react'

export function Modal({ isOpen, onClose, title, children, footer }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      requestAnimationFrame(() => setVisible(true))
    } else {
      setVisible(false)
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-200
        ${visible ? 'bg-black/50' : 'bg-black/0'}`}
      onClick={onClose}
    >
      <div
        className={`bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col
          transition-all duration-200
          ${visible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="px-6 py-4 overflow-y-auto flex-1">{children}</div>
        {footer && (
          <div className="px-6 py-4 border-t flex justify-end gap-2">{footer}</div>
        )}
      </div>
    </div>
  )
}
