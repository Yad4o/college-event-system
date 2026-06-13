import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getClub, joinClub } from '../api/clubs'
import { getEvents } from '../api/events'
import Navbar from '../components/Navbar'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

export default function ClubDetail() {
  const { id } = useParams<{ id: string }>()
  const clubId = Number(id)
  const qc = useQueryClient()

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
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-3xl mx-auto px-6 py-8 animate-pulse space-y-4">
          <div className="h-8 bg-gray-100 rounded w-1/3" />
          <div className="h-4 bg-gray-100 rounded w-2/3" />
        </div>
      </div>
    )
  }

  if (isError || !club) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="text-center py-24 text-red-500">Club not found.</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
          <div className="flex items-start gap-4">
            {club.logo_url ? (
              <img src={club.logo_url} alt={club.name} className="w-16 h-16 rounded-xl object-cover" />
            ) : (
              <div className="w-16 h-16 rounded-xl bg-blue-100 flex items-center justify-center">
                <span className="text-2xl font-bold text-blue-600">{club.name.charAt(0)}</span>
              </div>
            )}
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold text-gray-800">{club.name}</h1>
              {club.domain && (
                <span className="text-sm text-blue-500 capitalize">{club.domain}</span>
              )}
              {club.description && (
                <p className="text-sm text-gray-600 mt-2">{club.description}</p>
              )}
              <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
                <span>{club.member_count} member{club.member_count !== 1 ? 's' : ''}</span>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    club.join_type === 'open'
                      ? 'bg-green-50 text-green-600'
                      : 'bg-amber-50 text-amber-600'
                  }`}
                >
                  {club.join_type === 'open' ? 'Open to join' : 'Invite only'}
                </span>
              </div>
            </div>
            <button
              onClick={() => joinMut.mutate()}
              disabled={joinMut.isPending || joinMut.isSuccess}
              className="flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white transition-colors"
            >
              {joinMut.isSuccess
                ? 'Joined ✓'
                : joinMut.isPending
                ? 'Joining…'
                : 'Join'}
            </button>
          </div>
          {joinMut.isError && (
            <p className="mt-3 text-sm text-red-500">
              {(joinMut.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
                'Could not join club.'}
            </p>
          )}
        </div>

        {/* Upcoming events */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h2 className="font-semibold text-gray-700 mb-4">Upcoming events</h2>
          {!events || events.length === 0 ? (
            <p className="text-sm text-gray-400">No upcoming events.</p>
          ) : (
            <ul className="divide-y divide-gray-50">
              {events.map((ev) => (
                <li key={ev.id} className="py-3">
                  <Link
                    to={`/events/${ev.id}`}
                    className="flex items-center justify-between group"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-800 group-hover:text-blue-600 transition-colors">
                        {ev.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {formatDate(ev.start_at)}{ev.venue ? ` · ${ev.venue}` : ''}
                      </p>
                    </div>
                    <span className="text-xs text-gray-400">{ev.rsvp_count} RSVPs →</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
