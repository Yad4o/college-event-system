import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const NAV = [
  { to: '/', label: 'Dashboard' },
  { to: '/clubs', label: 'Clubs' },
  { to: '/events', label: 'Events' },
  { to: '/profile', label: 'Profile' },
]

export default function Navbar() {
  const { logout } = useAuth()
  const { pathname } = useLocation()

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-6">
      <span className="font-bold text-blue-600 text-sm tracking-tight mr-4">CES</span>
      {NAV.map(({ to, label }) => (
        <Link
          key={to}
          to={to}
          className={`text-sm font-medium transition-colors ${
            pathname === to || (to !== '/' && pathname.startsWith(to))
              ? 'text-blue-600'
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          {label}
        </Link>
      ))}
      <button
        onClick={logout}
        className="ml-auto text-sm text-gray-400 hover:text-red-500 transition-colors"
      >
        Sign out
      </button>
    </nav>
  )
}
