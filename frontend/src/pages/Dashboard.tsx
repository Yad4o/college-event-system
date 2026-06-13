
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMe } from '../api/users'
import { getEvents, type Event } from '../api/events'
import { getClubs, type Club } from '../api/clubs'
import { getNotifications, type Notification } from '../api/notifications'
import { getStats, type DashboardStats } from '../api/admin'
import Navbar from '../components/Navbar'

// ── helpers ───────────────────────────────────────────────────────────────────
function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    weekday: 'short', day: 'numeric', month: 'short',
  })
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

// ── sub-components ────────────────────────────────────────────────────────────
function SectionHeader({ title, to, linkLabel }: { title: string; to: string; linkLabel: string }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="font-semibold text-gray-700 text-base">{title}</h2>
      <Link to={to} className="text-xs text-blue-500 hover:text-blue-700 font-medium transition-colors">
        {linkLabel} →
      </Link>
    </div>
  )
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      {children}
    </div>
  )
}

// ── Upcoming RSVPs ─────────────────────────────────────────────────────────────
function UpcomingEvents() {
  const { data: events, isLoading } = useQuery({
    queryKey: ['events', { limit: 50 }],
    queryFn: () => getEvents({ limit: 50 }),
  })

  const upcoming = events
    ?.filter((e: Event) => !e.is_cancelled && new Date(e.start_at) > new Date())
    .slice(0, 4)

  return (
    <Card>
      <SectionHeader title="Upcoming Events" to="/events" linkLabel="All events" />
      {isLoading && (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-3">
              <div className="w-10 h-10 rounded-lg bg-gray-100 flex-shrink-0" />
              <div className="flex-1 space-y-1.5 py-0.5">
                <div className="h-3.5 bg-gray-100 rounded w-3/4" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      )}
      {!isLoading && (!upcoming || upcoming.length === 0) && (
        <p className="text-sm text-gray-400 py-2">No upcoming events. <Link to="/events" className="text-blue-500">Browse events</Link></p>
      )}
      {upcoming && upcoming.length > 0 && (
        <ul className="divide-y divide-gray-50">
          {upcoming.map((ev: Event) => (
            <li key={ev.id}>
              <Link
                to={`/events/${ev.id}`}
                className="flex items-center gap-3 py-2.5 group"
              >
                {/* Date block */}
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex flex-col items-center justify-center flex-shrink-0">
                  <span className="text-[10px] font-semibold text-blue-400 uppercase leading-none">
                    {new Date(ev.start_at).toLocaleDateString('en-IN', { month: 'short' })}
                  </span>
                  <span className="text-base font-bold text-blue-600 leading-none">
                    {new Date(ev.start_at).getDate()}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate group-hover:text-blue-600 transition-colors">
                    {ev.title}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {formatDate(ev.start_at)}{ev.venue ? ` · ${ev.venue}` : ''}
                  </p>
                </div>
                <span className="text-xs text-gray-300 flex-shrink-0">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

// ── My Clubs ──────────────────────────────────────────────────────────────────
function MyClubs() {
  const { data: clubs, isLoading } = useQuery({
    queryKey: ['clubs', {}],
    queryFn: () => getClubs({ limit: 50 }),
  })

  const shown = clubs?.slice(0, 4)

  return (
    <Card>
      <SectionHeader title="Clubs" to="/clubs" linkLabel="All clubs" />
      {isLoading && (
        <div className="space-y-3 animate-pulse">
          {[1, 2].map(i => (
            <div key={i} className="flex gap-3 items-center">
              <div className="w-8 h-8 rounded-lg bg-gray-100 flex-shrink-0" />
              <div className="h-3.5 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}
      {!isLoading && (!shown || shown.length === 0) && (
        <p className="text-sm text-gray-400 py-2">No clubs yet. <Link to="/clubs" className="text-blue-500">Browse clubs</Link></p>
      )}
      {shown && shown.length > 0 && (
        <ul className="divide-y divide-gray-50">
          {shown.map((c: Club) => (
            <li key={c.id}>
              <Link
                to={`/clubs/${c.id}`}
                className="flex items-center gap-3 py-2.5 group"
              >
                {c.logo_url ? (
                  <img src={c.logo_url} alt={c.name} className="w-8 h-8 rounded-lg object-cover flex-shrink-0" />
                ) : (
                  <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                    <span className="text-blue-600 font-bold text-xs">{c.name.charAt(0)}</span>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate group-hover:text-blue-600 transition-colors">
                    {c.name}
                  </p>
                  {c.domain && (
                    <p className="text-xs text-gray-400 capitalize">{c.domain}</p>
                  )}
                </div>
                <span className="text-xs text-gray-300 flex-shrink-0">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

// ── Recent Notifications ───────────────────────────────────────────────────────
function RecentNotifications() {
  const { data: notifications, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => import('../api/notifications').then(m => m.getNotifications()),
  })

  const recent = notifications?.slice(0, 4)
  const unread = notifications?.filter((n: Notification) => !n.is_read).length ?? 0

  return (
    <Card>
      <SectionHeader
        title={`Notifications${unread > 0 ? ` (${unread} new)` : ''}`}
        to="/notifications"
        linkLabel="See all"
      />
      {isLoading && (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="space-y-1.5">
              <div className="h-3.5 bg-gray-100 rounded w-3/4" />
              <div className="h-3 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}
      {!isLoading && (!recent || recent.length === 0) && (
        <p className="text-sm text-gray-400 py-2">No notifications yet.</p>
      )}
      {recent && recent.length > 0 && (
        <ul className="divide-y divide-gray-50">
          {recent.map((n: Notification) => (
            <li key={n.id} className="py-2.5 flex items-start gap-2">
              {!n.is_read && (
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0" />
              )}
              {n.is_read && (
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className={`text-sm truncate ${n.is_read ? 'text-gray-500' : 'text-gray-800 font-medium'}`}>
                  {n.title}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">{timeAgo(n.created_at)}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

// ── Admin Stats strip (college_admin only) ────────────────────────────────────
function AdminStrip() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: getStats,
    retry: false,
  })

  if (isLoading) return null
  if (isError || !data) return null

  const s: DashboardStats = data

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 mb-6">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Platform overview</p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Users',          value: s.total_users },
          { label: 'Active clubs',   value: s.active_clubs },
          { label: 'Upcoming events',value: s.upcoming_events },
          { label: 'Certificates',   value: s.total_certificates_issued },
        ].map(({ label, value }) => (
          <div key={label}>
            <p className="text-2xl font-bold text-gray-800">{value.toLocaleString()}</p>
            <p className="text-xs text-gray-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { data: me, isLoading: meLoading } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  })

  const isAdmin = me?.role === 'college_admin'
  const greeting = (() => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  })()

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Greeting */}
        <div className="mb-6">
          {meLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-7 bg-gray-100 rounded w-1/3" />
              <div className="h-4 bg-gray-100 rounded w-1/4" />
            </div>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-gray-800">
                {greeting}{me ? `, ${me.full_name.split(' ')[0]}` : ''}
              </h1>
              <p className="text-sm text-gray-400 mt-0.5">
                {new Date().toLocaleDateString('en-IN', {
                  weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
                })}
              </p>
            </>
          )}
        </div>

        {/* Admin stats strip — only renders if user is college_admin */}
        {isAdmin && <AdminStrip />}

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <UpcomingEvents />
          <div className="space-y-5">
            <MyClubs />
            <RecentNotifications />
          </div>
        </div>

        {/* Quick links footer */}
        <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { to: '/clubs',         label: 'Browse clubs',    emoji: '🏛️' },
            { to: '/events',        label: 'Find events',     emoji: '📅' },
            { to: '/notifications', label: 'Notifications',   emoji: '🔔' },
            { to: '/profile',       label: 'Your profile',    emoji: '👤' },
          ].map(({ to, label, emoji }) => (
            <Link
              key={to}
              to={to}
              className="flex items-center gap-2 bg-white rounded-xl border border-gray-100 shadow-sm px-4 py-3 text-sm font-medium text-gray-600 hover:shadow-md hover:text-blue-600 transition-all"
            >
              <span>{emoji}</span>
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
