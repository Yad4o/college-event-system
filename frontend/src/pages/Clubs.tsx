
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getClubs, type Club } from '../api/clubs'
import { getMe } from '../api/users'
import Navbar from '../components/Navbar'
import Seal from '../components/Seal'
import Tag from '../components/Tag'
import EmptyState from '../components/EmptyState'
import NewClubModal from '../components/NewClubModal'

const DOMAINS = ['', 'technical', 'cultural', 'sports', 'social', 'academic']

const DOMAIN_TONE: Record<string, 'rust' | 'pine' | 'gold' | 'slate' | 'neutral'> = {
  technical: 'slate',
  cultural:  'gold',
  sports:    'pine',
  social:    'rust',
  academic:  'neutral',
}

function ClubCard({ club }: { club: Club }) {
  return (
    <Link
      to={`/clubs/${club.id}`}
      className="pin-card group block rounded-2xl border border-ink/5 shadow-pin hover:shadow-pin-hover p-5 pt-7 transition-all hover:-translate-y-0.5"
    >
      <div className="flex items-start gap-3">
        <Seal name={club.name} logoUrl={club.logo_url} size="md" />
        <div className="min-w-0 flex-1 pt-1">
          <h3 className="font-display font-semibold text-ink truncate group-hover:text-rust transition-colors">
            {club.name}
          </h3>
          {club.domain && (
            <div className="mt-1">
              <Tag tone={DOMAIN_TONE[club.domain] ?? 'neutral'}>{club.domain}</Tag>
            </div>
          )}
        </div>
      </div>

      {club.description && (
        <p className="text-sm text-ink/55 mt-3 line-clamp-2 leading-relaxed">{club.description}</p>
      )}

      <div className="mt-4 pt-3 border-t border-dashed border-ink/10 flex items-center justify-between text-xs">
        <span className="font-mono text-ink/40">
          {club.member_count} member{club.member_count !== 1 ? 's' : ''}
        </span>
        <Tag tone={club.join_type === 'open' ? 'pine' : 'gold'}>
          {club.join_type === 'open' ? 'Open' : 'Invite only'}
        </Tag>
      </div>
    </Link>
  )
}

export default function Clubs() {
  const [domain, setDomain] = useState('')
  const [modalOpen, setModalOpen] = useState(false)

  const { data: me } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const isAdmin = me?.role === 'college_admin'

  const { data: clubs, isLoading, isError } = useQuery({
    queryKey: ['clubs', domain],
    queryFn: () => getClubs({ domain: domain || undefined, limit: 50 }),
  })

  return (
    <div className="min-h-screen bg-paper">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-start justify-between gap-4 mb-1">
          <div>
            <p className="stamp-label text-rust mb-1">The noticeboard</p>
            <h1 className="text-2xl sm:text-3xl font-display font-bold text-ink">Clubs</h1>
          </div>
          <button
            onClick={() => setModalOpen(true)}
            className="flex-shrink-0 inline-flex items-center gap-1.5 bg-ink hover:bg-ink/90 text-paper font-display font-semibold rounded-lg px-3.5 sm:px-4 py-2 text-sm transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
            <span className="hidden sm:inline">{isAdmin ? 'New club' : 'Pitch a club'}</span>
            <span className="sm:hidden">New</span>
          </button>
        </div>

        <p className="text-sm text-ink/45 mb-6">
          {clubs ? `${clubs.length} club${clubs.length !== 1 ? 's' : ''} on campus` : 'Browse what\'s active on campus'}
        </p>

        <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
          {DOMAINS.map((d) => (
            <button
              key={d}
              onClick={() => setDomain(d)}
              className={`flex-shrink-0 stamp-label px-3 py-1.5 rounded-full border transition-colors ${
                domain === d
                  ? 'bg-ink text-paper border-ink'
                  : 'bg-white text-ink/50 border-ink/10 hover:border-ink/30'
              }`}
            >
              {d ? d : 'All'}
            </button>
          ))}
        </div>

        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white rounded-2xl border border-ink/5 p-5 pt-7 animate-pulse">
                <div className="flex gap-3">
                  <div className="w-14 h-14 rounded-full bg-ink/5" />
                  <div className="flex-1 space-y-2 pt-1">
                    <div className="h-4 bg-ink/5 rounded w-3/4" />
                    <div className="h-3 bg-ink/5 rounded w-1/2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <EmptyState
            tone="error"
            title="Couldn't load the board"
            message="Something went wrong fetching clubs. Try refreshing."
            icon={
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              </svg>
            }
          />
        )}

        {clubs && clubs.length === 0 && (
          <EmptyState
            title="Nothing pinned here yet"
            message={isAdmin ? 'Add the first club to get the board started.' : 'No clubs in this domain yet — check back soon, or pitch one of your own.'}
            icon={
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" /><path d="M8 12h8M12 8v8" />
              </svg>
            }
            action={
              <button
                onClick={() => setModalOpen(true)}
                className="inline-flex items-center gap-1.5 bg-ink hover:bg-ink/90 text-paper font-display font-semibold rounded-lg px-4 py-2 text-sm transition-colors"
              >
                {isAdmin ? 'Add a club' : 'Pitch a club'}
              </button>
            }
          />
        )}

        {clubs && clubs.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {clubs.map((c) => (
              <ClubCard key={c.id} club={c} />
            ))}
          </div>
        )}
      </div>

      <NewClubModal open={modalOpen} onClose={() => setModalOpen(false)} isAdmin={isAdmin} />
    </div>
  )
}
