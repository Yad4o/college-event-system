
// A club's "seal" — a stamped crest in place of a generic logo square.
// Ring color is derived deterministically from the club name so each
// club gets a consistent, distinct seal without storing extra data.

const RING_COLORS = [
  '#FF6B35', // rust
  '#2D6A4F', // pine
  '#E0A458', // gold
  '#5B7FBE', // slate blue
  '#A8553B', // clay
  '#6B5B95', // plum
]

function colorForName(name: string): string {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = (hash * 31 + name.charCodeAt(i)) % RING_COLORS.length
  }
  return RING_COLORS[Math.abs(hash) % RING_COLORS.length]
}

interface SealProps {
  name: string
  logoUrl?: string | null
  size?: 'sm' | 'md' | 'lg'
}

const SIZES = {
  sm: { box: 'w-10 h-10', text: 'text-sm', ring: 2 },
  md: { box: 'w-14 h-14', text: 'text-lg', ring: 3 },
  lg: { box: 'w-20 h-20', text: 'text-2xl', ring: 3 },
}

export default function Seal({ name, logoUrl, size = 'md' }: SealProps) {
  const color = colorForName(name)
  const { box, text, ring } = SIZES[size]

  if (logoUrl) {
    return (
      <div
        className={`${box} rounded-full overflow-hidden flex-shrink-0`}
        style={{ boxShadow: `0 0 0 ${ring}px #fff, 0 0 0 ${ring + 2}px ${color}` }}
      >
        <img src={logoUrl} alt={name} className="w-full h-full object-cover" />
      </div>
    )
  }

  const initial = name.trim().charAt(0).toUpperCase()

  return (
    <div
      className={`${box} rounded-full flex-shrink-0 flex items-center justify-center bg-paper`}
      style={{ boxShadow: `0 0 0 ${ring}px #fff, 0 0 0 ${ring + 2}px ${color}` }}
    >
      <span className={`font-display font-bold ${text}`} style={{ color }}>
        {initial}
      </span>
    </div>
  )
}
