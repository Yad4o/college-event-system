
import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getClub, joinClub } from '../api/clubs'
import { getEvents } from '../api/events'
import { getMe } from '../api/users'
import Navbar from '../components/Navbar'
import Seal from '../components/Seal'
import Tag from '../components/Tag'
import EmptyState from '../components/EmptyState'
import JoinRequestsPanel from '../components/JoinRequestsPanel'
import NewEventModal from '../components/NewEventModal'

const DOMAIN_TONE: Record<string, 'rust' | 'pine' | 'gold' | 'slate' | 'neutral'> = {
  technical: 'slate',
  cultural:  'gold',
  sports:    'pine',
  social:    'rust',
  academic:  'neutral',
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

export default function ClubDetail() {
  const { id } = useParams<{ id: string }>()
  const clubId = Number(id)
  const qc = useQueryClient()
  const [eventModalOpen, setEventModalOpen] = useState(false)

  const { data: me } = useQuery({ queryKey: ['me'], queryFn: getMe })

  const { data: club, isLoading, isError } = useQuery({
    queryKey: ['club', clubId],
    queryFn: () => getClub(clubId),
    enabled: !isNaN(clubId),
  })

  const { data: events } = useQuery({
    queryKey: ['events', { club_id: clubId }],
    queryFn: () => getEvents({ club_id: clubId, limit: 5 }),
    enabled: !isNaN(clubId),
  })

  const joinMut = useMutation({
    mutationFn: () => joinClub(clubId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['club', clubId] }),
  })

  if (isLoading) {
    return (
      <div className="min-h-screen board-bg">
        <Navbar />
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 animate-pulse space-y-4">
          <div className="h-8 bg-ink/5 rounded w-1/3" />
          <div className="h-4 bg-ink/5 rounded w-2/3" />
        </div>
      </div>
    )
  }

  if (isError || !club) {
    return (
      <div className="min-h-screen board-bg">
        <Navbar />
        <EmptyState
          tone="error"
          title="This club isn't on the board"
          message="It may have been removed, or the link is incorrect."
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M15 9l-6 6M9 9l6 6" />
            </svg>
          }
          action={
            <Link to="/clubs" className="text-sm font-display font-semibold text-rust hover:underline">
              Back to clubs
            </Link>
          }
        />
      </div>
    )
  }

  const canPostEvents = me?.role === 'college_admin' || me?.role === 'club_admin'

  return (
    <div className="min-h-screen board-bg">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <Link to="/clubs" className="text-sm text-ink/40 hover:text-ink mb-4 inline-flex items-center gap-1 transition-colors">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/>
          </svg>
          Clubs
        </Link>

        {/* Header */}
        <div className="pin-card rounded-2xl border border-ink/5 shadow-pin p-6 pt-8 mb-6">
          <div className="flex items-start gap-4">
            <Seal name={club.name} logoUrl={club.logo_url} size="lg" />
            <div className="flex-1 min-w-0">
              <h1 className="text-xl sm:text-2xl font-display font-bold text-ink">{club.name}</h1>
              {club.domain && (
                <div className="mt-1.5">
                  <Tag tone={DOMAIN_TONE[club.domain] ?? 'neutral'}>{club.domain}</Tag>
                </div>
              )}
              {club.description && (
                <p className="text-sm text-ink/60 mt-3 leading-relaxed">{club.description}</p>
              )}
              <div className="mt-4 flex items-center gap-3 text-sm">
                <span className="font-mono text-ink/40">
                  {club.member_count} member{club.member_count !== 1 ? 's' : ''}
                </span>
                <Tag tone={club.join_type === 'open' ? 'pine' : 'gold'}>
                  {club.join_type === 'open' ? 'Open to join' : 'Invite only'}
                </Tag>
              </div>
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-dashed border-ink/10 flex flex-wrap gap-3">
            <button
              onClick={() => joinMut.mutate()}
              disabled={joinMut.isPending || joinMut.isSuccess}
              className="px-5 py-2 rounded-lg text-sm font-display font-semibold bg-rust hover:bg-rust/90 disabled:opacity-50 text-white transition-colors"
            >
              {joinMut.isSuccess
                ? 'Joined ✓'
                : joinMut.isPending
                ? 'Joining…'
                : club.join_type === 'open'
                ? 'Join club'
                : 'Request to join'}
            </button>

            {canPostEvents && (
              <button
                onClick={() => setEventModalOpen(true)}
                className="px-5 py-2 rounded-lg text-sm font-display font-semibold bg-white border border-ink/15 hover:border-ink/30 text-ink transition-colors"
              >
                + Pin an event
              </button>
            )}
          </div>

          {joinMut.isError && (
            <p className="mt-3 text-sm text-alert">
              {(joinMut.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
                'Could not join club.'}
            </p>
          )}
          {joinMut.isSuccess && club.join_type === 'invite_only' && (
            <p className="mt-3 text-sm text-pine">
              Request sent — the club president will review it.
            </p>
          )}
        </div>

        {/* Pending join requests — only renders for the club president */}
        <JoinRequestsPanel clubId={clubId} />

        {/* Upcoming events */}
        <div className="pin-card rounded-2xl border border-ink/5 shadow-pin p-6 pt-7">
          <p className="stamp-label text-rust mb-3">What's happening</p>
          {!events || events.length === 0 ? (
            <EmptyState
              title="No events pinned yet"
              message={canPostEvents ? 'Be the first to post one for this club.' : 'Check back soon for upcoming events.'}
              icon={
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="4" width="18" height="18" rx="2" />
                  <path d="M16 2v4M8 2v4M3 10h18" />
                </svg>
              }
            />
          ) : (
            <ul className="divide-y divide-dashed divide-ink/10">
              {events.map((ev) => (
                <li key={ev.id} className="py-3 first:pt-0 last:pb-0">
                  <Link
                    to={`/events/${ev.id}`}
                    className="flex items-center justify-between gap-3 group"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink group-hover:text-rust transition-colors truncate">
                        {ev.title}
                      </p>
                      <p className="text-xs text-ink/40 mt-0.5 font-mono">
                        {formatDate(ev.start_at)}{ev.venue ? ` · ${ev.venue}` : ''}
                      </p>
                    </div>
                    <span className="text-xs text-ink/40 font-mono flex-shrink-0">{ev.rsvp_count} RSVPs →</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {canPostEvents && (
        <NewEventModal
          open={eventModalOpen}
          onClose={() => setEventModalOpen(false)}
          clubId={clubId}
          clubName={club.name}
        />
      )}
    </div>
  )
}
