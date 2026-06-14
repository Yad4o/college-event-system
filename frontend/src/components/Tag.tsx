
interface TagProps {
  children: React.ReactNode
  tone?: 'rust' | 'pine' | 'gold' | 'alert' | 'neutral' | 'slate'
}

const TONE_CLASSES: Record<string, string> = {
  rust:    'bg-rust/10 text-rust',
  pine:    'bg-pine/10 text-pine',
  gold:    'bg-gold/15 text-[#9c6a1f]',
  alert:   'bg-alert/10 text-alert',
  neutral: 'bg-ink/5 text-ink/60',
  slate:   'bg-[#5B7FBE]/10 text-[#5B7FBE]',
}

export default function Tag({ children, tone = 'neutral' }: TagProps) {
  return (
    <span
      className={`stamp-label inline-flex items-center px-2 py-0.5 rounded-full ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  )
}
