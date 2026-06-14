
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getEvents, type Event } from '../api/events'
import { getClubs } from '../api/clubs'
import Navbar from '../components/Navbar'
import EmptyState from '../components/EmptyState'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    weekday: 'short', day: 'numeric', month: 'short',
  })
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
}

const FILTERS = [
  { id: 'upcoming', label: 'Upcoming' },
  { id: 'all',      label: 'All' },
] as const

function EventCard({ event, clubName }: { event: Event; clubName?: string }) {
  const date = new Date(event.start_at)
  const isFull = event.seat_limit != null && event.rsvp_count >= event.seat_limit

  return (
    <Link
      to={`/events/${event.id}`}
      className="pin-card group flex rounded-2xl border border-ink/5 shadow-pin hover:shadow-pin-hover transition-all hover:-translate-y-0.5 overflow-hidden"
    >
      {/* Ticket stub — date block */}
      <div className="flex-shrink-0 w-20 bg-ink flex flex-col items-center justify-center py-4 relative">
        <span className="stamp-label text-paper/50">
          {date.toLocaleDateString('en-IN', { month: 'short' })}
        </span>
        <span className="font-display font-bold text-3xl text-paper leading-none mt-0.5">
          {date.getDate()}
        </span>
        <span className="text-[10px] text-paper/40 font-mono mt-1">
          {date.toLocaleDateString('en-IN', { weekday: 'short' })}
        </span>
        {/* perforation */}
        <div className="absolute right-0 top-0 bottom-0 flex flex-col justify-between py-1">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="w-1.5 h-1.5 rounded-full bg-paper -mr-[3px]" />
          ))}
        </div>
      </div>

      <div className="flex-1 p-4 pt-5 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-display font-semibold text-ink leading-snug group-hover:text-rust transition-colors">
            {event.title}
          </h3>
          {event.is_cancelled && (
            <span className="flex-shrink-0 stamp-label px-2 py-0.5 bg-alert/10 text-alert rounded-full">
              Cancelled
            </span>
          )}
        </div>

        {clubName && <p className="text-xs text-ink/40 mt-0.5">{clubName}</p>}

        {event.description && (
          <p className="text-sm text-ink/55 mt-1.5 line-clamp-2 leading-relaxed">{event.description}</p>
        )}

        <div className="mt-2.5 flex items-center gap-3 text-xs text-ink/40 font-mono">
          <span>{formatDate(event.start_at)} · {formatTime(event.start_at)}</span>
          {event.venue && <span className="truncate">📍 {event.venue}</span>}
        </div>

        <div className="mt-2.5 flex items-center gap-2 text-xs">
          <span className={`stamp-label px-2 py-0.5 rounded-full ${isFull ? 'bg-alert/10 text-alert' : 'bg-pine/10 text-pine'}`}>
            {isFull ? 'Full' : `${event.rsvp_count} going`}
          </span>
          {event.waitlist_count > 0 && (
            <span className="stamp-label px-2 py-0.5 bg-gold/15 text-[#9c6a1f] rounded-full">
              {event.waitlist_count} waitlisted
            </span>
          )}
          {event.seat_limit && !isFull && (
            <span className="text-ink/30 font-mono">{event.seat_limit - event.rsvp_count} left</span>
          )}
        </div>
      </div>
    </Link>
  )
}

export default function Events() {
  const [filter, setFilter] = useState<'upcoming' | 'all'>('upcoming')

  const { data: events, isLoading, isError } = useQuery({
    queryKey: ['events'],
    queryFn: () => getEvents({ limit: 50 }),
  })

  const { data: clubs } = useQuery({
    queryKey: ['clubs', {}],
    queryFn: () => getClubs({ limit: 100 }),
  })

  const clubNameById = new Map(clubs?.map((c) => [c.id, c.name]) ?? [])

  const filtered = events?.filter((e) => {
    if (filter === 'all') return true
    return !e.is_cancelled && new Date(e.start_at) > new Date()
  })

  const sorted = filtered
    ?.slice()
    .sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime())

  return (
    <div className="min-h-screen bg-paper">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <p className="stamp-label text-rust mb-1">What's on</p>
        <h1 className="text-2xl sm:text-3xl font-display font-bold text-ink mb-1">Events</h1>
        <p className="text-sm text-ink/45 mb-5">
          {sorted ? `${sorted.length} event${sorted.length !== 1 ? 's' : ''}` : 'Across every club on campus'}
        </p>

        <div className="flex gap-2 mb-6">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`stamp-label px-3 py-1.5 rounded-full border transition-colors ${
                filter === f.id
                  ? 'bg-ink text-paper border-ink'
                  : 'bg-white text-ink/50 border-ink/10 hover:border-ink/30'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {isLoading && (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex bg-white rounded-2xl border border-ink/5 overflow-hidden animate-pulse h-24">
                <div className="w-20 bg-ink/5 flex-shrink-0" />
                <div className="flex-1 p-4 space-y-2">
                  <div className="h-4 bg-ink/5 rounded w-2/3" />
                  <div className="h-3 bg-ink/5 rounded w-1/2" />
                  <div className="h-3 bg-ink/5 rounded w-1/3" />
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <EmptyState
            tone="error"
            title="Couldn't load events"
            message="Something went wrong. Try refreshing the page."
            icon={
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              </svg>
            }
          />
        )}

        {sorted && sorted.length === 0 && (
          <EmptyState
            title={filter === 'upcoming' ? 'Nothing coming up' : 'No events yet'}
            message={
              filter === 'upcoming'
                ? 'No upcoming events right now — switch to "All" to see past events, or check back soon.'
                : 'Once a club pins an event here, it\\'ll show up for everyone.'
            }
            icon={
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" />
              </svg>
            }
          />
        )}

        {sorted && sorted.length > 0 && (
          <div className="space-y-3">
            {sorted.map((e) => (
              <EventCard key={e.id} event={e} clubName={clubNameById.get(e.club_id)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
