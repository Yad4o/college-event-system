import { useAuth } from '../hooks/useAuth'

export default function Dashboard() {
  const { logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
          <button
            onClick={logout}
            className="text-sm text-gray-500 hover:text-red-600 transition-colors"
          >
            Sign out
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <a href="/clubs" className="rounded-xl bg-white shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <h2 className="font-semibold text-gray-700 mb-1">Clubs</h2>
            <p className="text-sm text-gray-500">Browse and join clubs</p>
          </a>
          <a href="/events" className="rounded-xl bg-white shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
            <h2 className="font-semibold text-gray-700 mb-1">Events</h2>
            <p className="text-sm text-gray-500">Upcoming events & RSVPs</p>
          </a>
        </div>
      </div>
    </div>
  )
}
