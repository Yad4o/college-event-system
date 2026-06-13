import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getClubs, type Club } from '../api/clubs'
import Navbar from '../components/Navbar'

const DOMAINS = ['', 'technical', 'cultural', 'sports', 'social', 'academic']

function ClubCard({ club }: { club: Club }) {
  return (
    <Link
      to={`/clubs/${club.id}`}
      className="block bg-white rounded-xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start gap-3">
        {club.logo_url ? (
          <img
            src={club.logo_url}
            alt={club.name}
            className="w-10 h-10 rounded-lg object-cover flex-shrink-0"
          />
        ) : (
          <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
            <span className="text-blue-600 font-bold text-sm">
              {club.name.charAt(0).toUpperCase()}
            </span>
          </div>
        )}
        <div className="min-w-0">
          <h3 className="font-semibold text-gray-800 truncate">{club.name}</h3>
          {club.domain && (
            <span className="text-xs text-blue-500 capitalize">{club.domain}</span>
          )}
          {club.description && (
            <p className="text-sm text-gray-500 mt-1 line-clamp-2">{club.description}</p>
          )}
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
        <span>{club.member_count} member{club.member_count !== 1 ? 's' : ''}</span>
        <span
          className={`px-2 py-0.5 rounded-full font-medium ${
            club.join_type === 'open'
              ? 'bg-green-50 text-green-600'
              : 'bg-amber-50 text-amber-600'
          }`}
        >
          {club.join_type === 'open' ? 'Open' : 'Invite only'}
        </span>
      </div>
    </Link>
  )
}

export default function Clubs() {
  const [domain, setDomain] = useState('')

  const { data: clubs, isLoading, isError } = useQuery({
    queryKey: ['clubs', domain],
    queryFn: () => getClubs({ domain: domain || undefined, limit: 50 }),
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Clubs</h1>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {DOMAINS.map((d) => (
              <option key={d} value={d}>
                {d ? d.charAt(0).toUpperCase() + d.slice(1) : 'All domains'}
              </option>
            ))}
          </select>
        </div>

        {isLoading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-5 animate-pulse">
                <div className="flex gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gray-100" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-100 rounded w-3/4" />
                    <div className="h-3 bg-gray-100 rounded w-1/2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {isError && (
          <div className="text-center py-16 text-red-500">Failed to load clubs.</div>
        )}

        {clubs && clubs.length === 0 && (
          <div className="text-center py-16 text-gray-400">No clubs found.</div>
        )}

        {clubs && clubs.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {clubs.map((c) => (
              <ClubCard key={c.id} club={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
