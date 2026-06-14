
import type { ReactNode } from 'react'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  message?: string
  action?: ReactNode
  tone?: 'default' | 'error'
}

export default function EmptyState({ icon, title, message, action, tone = 'default' }: EmptyStateProps) {
  return (
    <div className="text-center py-16 px-6">
      {icon && (
        <div className={`mx-auto mb-3 w-12 h-12 flex items-center justify-center rounded-full ${
          tone === 'error' ? 'bg-alert/10 text-alert' : 'bg-rust/10 text-rust'
        }`}>
          {icon}
        </div>
      )}
      <p className={`font-display font-semibold ${tone === 'error' ? 'text-alert' : 'text-ink'}`}>
        {title}
      </p>
      {message && (
        <p className="text-sm text-ink/50 mt-1 max-w-sm mx-auto">{message}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
