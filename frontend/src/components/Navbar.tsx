
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useQuery } from '@tanstack/react-query'
import { getMe } from '../api/users'
import { getNotifications } from '../api/notifications'

const NAV = [
  { to: '/',       label: 'Board' },
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
    <nav className="bg-paper/95 backdrop-blur-sm border-b-2 border-ink/10 px-4 sm:px-6 sticky top-0 z-30">
      <div className="max-w-5xl mx-auto flex items-center gap-1 sm:gap-2 h-14">
        {/* Brand mark — looks like a stamped seal */}
        <Link to="/" className="flex items-center gap-2 mr-2 sm:mr-5 flex-shrink-0">
          <div className="w-8 h-8 rounded-full border-2 border-rust flex items-center justify-center">
            <span className="font-display font-bold text-sm text-rust">C</span>
          </div>
          <span className="hidden sm:inline font-display font-bold text-sm text-ink tracking-tight">
            Campus Board
          </span>
        </Link>

        <div className="flex items-center gap-0.5 sm:gap-1 overflow-x-auto">
          {NAV.map(({ to, label }) => {
            const active = pathname === to || (to !== '/' && pathname.startsWith(to))
            return (
              <Link
                key={to}
                to={to}
                className={`relative px-2.5 sm:px-3 py-2 text-sm font-medium font-display transition-colors whitespace-nowrap ${
                  active ? 'text-ink' : 'text-ink/45 hover:text-ink'
                }`}
              >
                {label}
                {active && (
                  <span className="absolute left-2.5 right-2.5 sm:left-3 sm:right-3 -bottom-px h-0.5 bg-rust rounded-full" />
                )}
              </Link>
            )
          })}

          {isAdmin && (
            <Link
              to="/admin"
              className={`relative px-2.5 sm:px-3 py-2 text-sm font-medium font-display transition-colors whitespace-nowrap ${
                pathname.startsWith('/admin') ? 'text-ink' : 'text-ink/45 hover:text-ink'
              }`}
            >
              Admin
              {pathname.startsWith('/admin') && (
                <span className="absolute left-2.5 right-2.5 sm:left-3 sm:right-3 -bottom-px h-0.5 bg-rust rounded-full" />
              )}
            </Link>
          )}
        </div>

        <div className="ml-auto flex items-center gap-3 sm:gap-4 flex-shrink-0">
          {/* Notification bell */}
          <Link
            to="/notifications"
            className={`relative transition-colors ${
              pathname === '/notifications' ? 'text-rust' : 'text-ink/45 hover:text-ink'
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
              <span className="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 flex items-center justify-center rounded-full bg-rust text-white text-[10px] font-bold px-1 leading-none font-mono">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </Link>

          {/* User pill */}
          {me && (
            <div className="hidden sm:flex items-center gap-2 pl-3 border-l border-ink/10">
              <div className="w-7 h-7 rounded-full bg-ink flex items-center justify-center flex-shrink-0">
                <span className="font-display font-bold text-xs text-paper">
                  {me.full_name.charAt(0).toUpperCase()}
                </span>
              </div>
              <span className="text-sm font-medium text-ink/70 max-w-[100px] truncate">
                {me.full_name.split(' ')[0]}
              </span>
            </div>
          )}

          <button
            onClick={logout}
            className="text-sm text-ink/40 hover:text-alert transition-colors font-medium"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}
