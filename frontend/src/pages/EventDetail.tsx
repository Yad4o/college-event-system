
import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getEvent, rsvpToEvent, cancelRsvp, type Rsvp } from '../api/events'
import { getClub } from '../api/clubs'
import Navbar from '../components/Navbar'
import Seal from '../components/Seal'
import Tag from '../components/Tag'
import EmptyState from '../components/EmptyState'

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function RsvpButton({
  eventId,
  isCancelled,
  isFull,
}: {
  eventId: number
  isCancelled: boolean
  isFull: boolean
}) {
  const qc = useQueryClient()

  const [rsvp, setRsvp] = useState<Rsvp | null>(null)
  const [actionError, setActionError] = useState('')

  const rsvpMut = useMutation({
    mutationFn: () => rsvpToEvent(eventId),
    onSuccess: (data) => {
      setRsvp(data)
      setActionError('')
      qc.invalidateQueries({ queryKey: ['event', eventId] })
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Could not RSVP. Please try again.'
      setActionError(detail)
    },
  })

  const cancelMut = useMutation({
    mutationFn: () => cancelRsvp(eventId),
    onSuccess: () => {
      setRsvp(null)
      setActionError('')
      qc.invalidateQueries({ queryKey: ['event', eventId] })
    },
    onError: () => setActionError('Could not cancel RSVP. Please try again.'),
  })

  if (isCancelled) return null

  const isPending = rsvpMut.isPending || cancelMut.isPending

  return (
    <div className="mt-6 pt-5 border-t border-dashed border-ink/10">
      {actionError && (
        <p className="mb-3 text-sm text-alert">{actionError}</p>
      )}

      {rsvp === null && (
        <button
          onClick={() => rsvpMut.mutate()}
          disabled={isPending || isFull}
          className="w-full sm:w-auto px-6 py-2.5 rounded-lg text-sm font-display font-semibold bg-rust hover:bg-rust/90 disabled:opacity-50 text-white transition-colors"
        >
          {isPending ? 'Saving…' : isFull ? 'Event full' : 'RSVP to this event'}
        </button>
      )}

      {rsvp?.status === 'confirmed' && (
        <div className="flex flex-wrap items-center gap-4">
          <span className="inline-flex items-center gap-1.5 text-sm text-pine font-display font-semibold">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
            You're confirmed
          </span>
          <button
            onClick={() => cancelMut.mutate()}
            disabled={isPending}
            className="text-sm text-ink/40 hover:text-alert disabled:opacity-50 transition-colors"
          >
            {isPending ? 'Cancelling…' : 'Cancel RSVP'}
          </button>
        </div>
      )}

      {rsvp?.status === 'waitlisted' && (
        <div className="flex flex-wrap items-center gap-4">
          <span className="text-sm text-[#9c6a1f] font-display font-semibold">
            On the waitlist
            {rsvp.waitlist_position != null ? ` — position ${rsvp.waitlist_position}` : ''}
          </span>
          <button
            onClick={() => cancelMut.mutate()}
            disabled={isPending}
            className="text-sm text-ink/40 hover:text-alert disabled:opacity-50 transition-colors"
          >
            {isPending ? 'Removing…' : 'Leave waitlist'}
          </button>
        </div>
      )}
    </div>
  )
}

export default function EventDetail() {
  const { id } = useParams<{ id: string }>()
  const eventId = Number(id)

  const { data: event, isLoading, isError } = useQuery({
    queryKey: ['event', eventId],
    queryFn: () => getEvent(eventId),
    enabled: !isNaN(eventId),
  })

  const { data: club } = useQuery({
    queryKey: ['club', event?.club_id],
    queryFn: () => getClub(event!.club_id),
    enabled: !!event?.club_id,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-paper">
        <Navbar />
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 animate-pulse space-y-4">
          <div className="h-8 bg-ink/5 rounded w-2/3" />
          <div className="h-4 bg-ink/5 rounded w-1/2" />
          <div className="h-40 bg-ink/5 rounded-2xl" />
        </div>
      </div>
    )
  }

  if (isError || !event) {
    return (
      <div className="min-h-screen bg-paper">
        <Navbar />
        <EmptyState
          tone="error"
          title="This event isn't on the board"
          message="It may have been removed, or the link is incorrect."
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" /><path d="M15 9l-6 6M9 9l6 6" />
            </svg>
          }
          action={
            <Link to="/events" className="text-sm font-display font-semibold text-rust hover:underline">
              Back to events
            </Link>
          }
        />
      </div>
    )
  }

  const date = new Date(event.start_at)
  const isFull = event.seat_limit != null && event.rsvp_count >= event.seat_limit

  return (
    <div className="min-h-screen bg-paper">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <Link to="/events" className="text-sm text-ink/40 hover:text-ink mb-4 inline-flex items-center gap-1 transition-colors">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
          Events
        </Link>

        <div className="pin-card rounded-2xl border border-ink/5 shadow-pin overflow-hidden">
          {/* Header strip with date block */}
          <div className="flex items-stretch">
            <div className="flex-shrink-0 w-24 bg-ink flex flex-col items-center justify-center py-5">
              <span className="stamp-label text-paper/50">
                {date.toLocaleDateString('en-IN', { month: 'short' })}
              </span>
              <span className="font-display font-bold text-4xl text-paper leading-none mt-1">
                {date.getDate()}
              </span>
              <span className="text-xs text-paper/40 font-mono mt-1">
                {date.toLocaleDateString('en-IN', { weekday: 'long' })}
              </span>
            </div>
            <div className="flex-1 p-5 pt-6 min-w-0">
              {event.is_cancelled && (
                <div className="mb-3 inline-flex items-center gap-1.5 stamp-label px-2.5 py-1 bg-alert/10 text-alert rounded-full">
                  Cancelled
                </div>
              )}
              <h1 className="text-xl sm:text-2xl font-display font-bold text-ink leading-snug">{event.title}</h1>

              {club && (
                <Link to={`/clubs/${club.id}`} className="mt-2 inline-flex items-center gap-2 group">
                  <Seal name={club.name} logoUrl={club.logo_url} size="sm" />
                  <span className="text-sm text-ink/50 group-hover:text-rust transition-colors">{club.name}</span>
                </Link>
              )}
            </div>
          </div>

          <div className="px-5 sm:px-6 pb-6">
            {event.description && (
              <p className="text-sm text-ink/65 leading-relaxed pt-1">{event.description}</p>
            )}

            <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="stamp-label text-ink/35 mb-1">When</dt>
                <dd className="text-ink font-medium">{formatDate(event.start_at)}</dd>
              </div>
              {event.venue && (
                <div>
                  <dt className="stamp-label text-ink/35 mb-1">Where</dt>
                  <dd className="text-ink font-medium">{event.venue}</dd>
                </div>
              )}
              {event.end_at && (
                <div className="col-span-2">
                  <dt className="stamp-label text-ink/35 mb-1">Ends</dt>
                  <dd className="text-ink font-medium">{formatDate(event.end_at)}</dd>
                </div>
              )}
            </dl>

            <div className="mt-4 flex items-center gap-2 flex-wrap">
              <Tag tone={isFull ? 'alert' : 'pine'}>
                {isFull ? 'Full' : `${event.rsvp_count} confirmed`}
              </Tag>
              {event.waitlist_count > 0 && (
                <Tag tone="gold">{event.waitlist_count} waitlisted</Tag>
              )}
              {event.seat_limit && (
                <span className="text-xs text-ink/40 font-mono">
                  / {event.seat_limit} seats
                </span>
              )}
              {event.event_type && event.event_type !== 'open' && (
                <Tag tone="slate">{event.event_type.replace('_', ' ')}</Tag>
              )}
            </div>

            {event.tags && event.tags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {event.tags.map((tag) => (
                  <span key={tag} className="text-xs px-2 py-0.5 bg-ink/5 text-ink/50 rounded-full font-mono">
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {event.is_cancelled && (
              <div className="mt-5 rounded-lg bg-alert/10 border border-alert/20 text-alert px-4 py-3 text-sm font-medium">
                This event has been cancelled by the organisers.
              </div>
            )}

            <RsvpButton
              eventId={eventId}
              isCancelled={event.is_cancelled}
              isFull={isFull}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
