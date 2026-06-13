import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getEvents, type Event } from '../api/events'
import Navbar from '../components/Navbar'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
  })
}

function EventCard({ event }: { event: Event }) {
  return (
    <Link
      to={`/events/${event.id}`}
      className="block bg-white rounded-xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-800 leading-snug">{event.title}</h3>
        {event.is_cancelled && (
          <span className="flex-shrink-0 text-xs px-2 py-0.5 bg-red-50 text-red-500 rounded-full font-medium">
            Cancelled
          </span>
        )}
      </div>
      {event.description && (
        <p className="text-sm text-gray-500 mt-1 line-clamp-2">{event.description}</p>
      )}
      <div className="mt-3 space-y-1 text-xs text-gray-400">
        <p>{formatDate(event.start_at)}</p>
        {event.venue && <p>📍 {event.venue}</p>}
      </div>
      <div className="mt-3 flex items-center gap-3 text-xs">
        <span className="text-gray-500">{event.rsvp_count} confirmed</span>
        {event.waitlist_count > 0 && (
          <span className="text-amber-500">{event.waitlist_count} waitlisted</span>
        )}
        {event.seat_limit && (
          <span className="ml-auto text-gray-400">{event.seat_limit} seats</span>
        )}
      </div>
    </Link>
  )
}

export default function Events() {
  const { data: events, isLoading, isError } = useQuery({
    queryKey: ['events'],
    queryFn: () => getEvents({ limit: 50 }),
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Events</h1>

        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 animate-pulse space-y-3">
                <div className="h-4 bg-gray-100 rounded w-3/4" />
                <div className="h-3 bg-gray-100 rounded w-full" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="text-center py-16 text-red-500">Failed to load events.</div>
        )}

        {events && events.length === 0 && (
          <div className="text-center py-16 text-gray-400">No events found.</div>
        )}

        {events && events.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {events.map((e) => (
              <EventCard key={e.id} event={e} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
