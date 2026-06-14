
import { useEffect, type ReactNode } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  eyebrow?: string
  children: ReactNode
}

export default function Modal({ open, onClose, title, eyebrow, children }: ModalProps) {
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-ink/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative w-full max-w-lg max-h-[85vh] overflow-y-auto bg-paper rounded-2xl shadow-pin-hover border border-ink/5 animate-[modal-in_0.18s_ease-out]"
      >
        <div className="sticky top-0 bg-paper border-b border-ink/5 px-6 py-4 flex items-start justify-between">
          <div>
            {eyebrow && <p className="stamp-label text-rust mb-1">{eyebrow}</p>}
            <h2 className="font-display font-bold text-lg text-ink">{title}</h2>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-ink/40 hover:text-ink transition-colors p-1 -mr-1 -mt-1"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>

      <style>{`
        @keyframes modal-in {
          from { opacity: 0; transform: translateY(8px) scale(0.98); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  )
}
