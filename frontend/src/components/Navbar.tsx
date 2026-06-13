import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useQuery } from '@tanstack/react-query'
import { getMe } from '../api/users'
import { getNotifications } from '../api/notifications'

const NAV = [
  { to: '/',       label: 'Dashboard' },
  { to: '/clubs',  label: 'Clubs' },
  { to: '/events', label: 'Events' },
  { to: '/profile',label: 'Profile' },
]

export default function Navbar() {
  const { logout } = useAuth()
  const { pathname } = useLocation()

  const { data: me } = useQuery({ queryKey: ['me'], queryFn: getMe })
  const isAdmin = me?.role === 'college_admin'

  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: getNotifications,
    refetchInterval: 60_000,
  })
  const unreadCount = notifications?.filter((n) => !n.is_read).length ?? 0

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

      {isAdmin && (
        <Link
          to="/admin"
          className={`text-sm font-medium transition-colors ${
            pathname.startsWith('/admin')
              ? 'text-blue-600'
              : 'text-gray-500 hover:text-gray-800'
          }`}
        >
          Admin
        </Link>
      )}

      {/* Notification bell */}
      <Link
        to="/notifications"
        className={`relative ml-auto text-sm font-medium transition-colors ${
          pathname === '/notifications'
            ? 'text-blue-600'
            : 'text-gray-500 hover:text-gray-800'
        }`}
        aria-label="Notifications"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.8}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold px-1 leading-none">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </Link>

      <button
        onClick={logout}
        className="text-sm text-gray-400 hover:text-red-500 transition-colors"
      >
        Sign out
      </button>
    </nav>
  )
}
