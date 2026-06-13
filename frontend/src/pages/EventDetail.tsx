import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getEvent, rsvpToEvent, cancelRsvp, type Rsvp } from '../api/events'
import Navbar from '../components/Navbar'

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
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

  // Local RSVP state — drives button label without an extra /rsvps API call
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
    <div className="mt-6">
      {actionError && (
        <p className="mb-3 text-sm text-red-500">{actionError}</p>
      )}

      {rsvp === null && (
        <button
          onClick={() => rsvpMut.mutate()}
          disabled={isPending || isFull}
          className="px-5 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white transition-colors"
        >
          {isPending ? 'Saving…' : isFull ? 'Event full' : 'RSVP'}
        </button>
      )}

      {rsvp?.status === 'confirmed' && (
        <div className="flex items-center gap-4">
          <span className="text-sm text-green-600 font-medium">
            ✓ You are confirmed
          </span>
          <button
            onClick={() => cancelMut.mutate()}
            disabled={isPending}
            className="text-sm text-gray-400 hover:text-red-500 disabled:opacity-50 transition-colors"
          >
            {isPending ? 'Cancelling…' : 'Cancel RSVP'}
          </button>
        </div>
      )}

      {rsvp?.status === 'waitlisted' && (
        <div className="flex items-center gap-4">
          <span className="text-sm text-amber-600 font-medium">
            You are on the waitlist
            {rsvp.waitlist_position != null
              ? ` (position ${rsvp.waitlist_position})`
              : ''}
          </span>
          <button
            onClick={() => cancelMut.mutate()}
            disabled={isPending}
            className="text-sm text-gray-400 hover:text-red-500 disabled:opacity-50 transition-colors"
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-2xl mx-auto px-6 py-8 animate-pulse space-y-4">
          <div className="h-8 bg-gray-100 rounded w-2/3" />
          <div className="h-4 bg-gray-100 rounded w-1/2" />
          <div className="h-32 bg-gray-100 rounded" />
        </div>
      </div>
    )
  }

  if (isError || !event) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="text-center py-24 text-red-500">Event not found.</div>
      </div>
    )
  }

  const isFull =
    event.seat_limit != null && event.rsvp_count >= event.seat_limit

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        <Link
          to="/events"
          className="text-sm text-gray-400 hover:text-gray-600 mb-4 inline-block"
        >
          ← Back to events
        </Link>

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          {event.is_cancelled && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-600 px-4 py-3 text-sm font-medium">
              This event has been cancelled.
            </div>
          )}

          <h1 className="text-2xl font-bold text-gray-800">{event.title}</h1>

          {event.event_type && (
            <span className="inline-block mt-1 text-xs px-2 py-0.5 bg-blue-50 text-blue-500 rounded-full capitalize">
              {event.event_type}
            </span>
          )}

          {event.description && (
            <p className="mt-4 text-gray-600 text-sm leading-relaxed">
              {event.description}
            </p>
          )}

          <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-gray-400 font-medium uppercase tracking-wide">
                Start
              </dt>
              <dd className="text-gray-700 mt-0.5">{formatDate(event.start_at)}</dd>
            </div>
            {event.end_at && (
              <div>
                <dt className="text-xs text-gray-400 font-medium uppercase tracking-wide">
                  End
                </dt>
                <dd className="text-gray-700 mt-0.5">{formatDate(event.end_at)}</dd>
              </div>
            )}
            {event.venue && (
              <div className="col-span-2">
                <dt className="text-xs text-gray-400 font-medium uppercase tracking-wide">
                  Venue
                </dt>
                <dd className="text-gray-700 mt-0.5">{event.venue}</dd>
              </div>
            )}
          </dl>

          <div className="mt-5 flex items-center gap-4 text-sm text-gray-500 border-t border-gray-50 pt-4">
            <span>{event.rsvp_count} confirmed</span>
            {event.waitlist_count > 0 && (
              <span className="text-amber-500">
                {event.waitlist_count} on waitlist
              </span>
            )}
            {event.seat_limit && (
              <span className={isFull ? 'text-red-500 font-medium' : ''}>
                {isFull
                  ? 'Full'
                  : `${event.seat_limit - event.rsvp_count} spots left`}
              </span>
            )}
          </div>

          {event.tags && event.tags.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {event.tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full"
                >
                  {tag}
                </span>
              ))}
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
  )
}
