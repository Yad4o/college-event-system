import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Dashboard</h1>
        <p className="text-gray-500 text-sm mb-8">Welcome to the College Event System.</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link
            to="/clubs"
            className="rounded-xl bg-white shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow"
          >
            <h2 className="font-semibold text-gray-700 mb-1">Clubs</h2>
            <p className="text-sm text-gray-500">Browse and join student clubs</p>
          </Link>
          <Link
            to="/events"
            className="rounded-xl bg-white shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow"
          >
            <h2 className="font-semibold text-gray-700 mb-1">Events</h2>
            <p className="text-sm text-gray-500">Upcoming events and RSVPs</p>
          </Link>
        </div>
      </div>
    </div>
  )
}
