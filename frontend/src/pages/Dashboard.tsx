
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMe } from '../api/users'
import { getEvents, type Event } from '../api/events'
import { getClubs, type Club } from '../api/clubs'
import { getNotifications, type Notification } from '../api/notifications'
import { getStats, type DashboardStats } from '../api/admin'
import Navbar from '../components/Navbar'
import Seal from '../components/Seal'
import EmptyState from '../components/EmptyState'

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
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

function SectionHeader({ title, to, linkLabel }: { title: string; to: string; linkLabel: string }) {
  return (
    <div className="flex items-center justify-between mb-3">
      <p className="stamp-label text-rust">{title}</p>
      <Link to={to} className="text-xs font-display font-semibold text-ink/40 hover:text-rust transition-colors">
        {linkLabel} →
      </Link>
    </div>
  )
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="pin-card rounded-2xl border border-ink/5 shadow-pin p-5 pt-7">
      {children}
    </div>
  )
}

// ── Upcoming Events ────────────────────────────────────────────────────────
function UpcomingEvents() {
  const { data: events, isLoading } = useQuery({
    queryKey: ['events', { limit: 50 }],
    queryFn: () => getEvents({ limit: 50 }),
  })

  const upcoming = events
    ?.filter((e: Event) => !e.is_cancelled && new Date(e.start_at) > new Date())
    .sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime())
    .slice(0, 4)

  return (
    <Card>
      <SectionHeader title="What's coming up" to="/events" linkLabel="All events" />
      {isLoading && (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-3">
              <div className="w-11 h-11 rounded-lg bg-ink/5 flex-shrink-0" />
              <div className="flex-1 space-y-1.5 py-0.5">
                <div className="h-3.5 bg-ink/5 rounded w-3/4" />
                <div className="h-3 bg-ink/5 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      )}
      {!isLoading && (!upcoming || upcoming.length === 0) && (
        <EmptyState
          title="Nothing pinned yet"
          message="No upcoming events right now."
          action={<Link to="/events" className="text-sm font-display font-semibold text-rust hover:underline">Browse events</Link>}
        />
      )}
      {upcoming && upcoming.length > 0 && (
        <ul className="divide-y divide-dashed divide-ink/10">
          {upcoming.map((ev: Event) => (
            <li key={ev.id}>
              <Link
                to={`/events/${ev.id}`}
                className="flex items-center gap-3 py-2.5 group"
              >
                <div className="w-11 h-11 rounded-lg bg-ink flex flex-col items-center justify-center flex-shrink-0">
                  <span className="text-[9px] font-semibold text-paper/50 uppercase leading-none stamp-label">
                    {new Date(ev.start_at).toLocaleDateString('en-IN', { month: 'short' })}
                  </span>
                  <span className="text-lg font-display font-bold text-paper leading-none mt-0.5">
                    {new Date(ev.start_at).getDate()}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-ink truncate group-hover:text-rust transition-colors">
                    {ev.title}
                  </p>
                  <p className="text-xs text-ink/40 mt-0.5 font-mono">
                    {formatTime(ev.start_at)}{ev.venue ? ` · ${ev.venue}` : ''}
                  </p>
                </div>
                <span className="text-xs text-ink/30 flex-shrink-0">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

// ── Clubs ──────────────────────────────────────────────────────────────────
function MyClubs() {
  const { data: clubs, isLoading } = useQuery({
    queryKey: ['clubs', {}],
    queryFn: () => getClubs({ limit: 50 }),
  })

  const shown = clubs?.slice(0, 4)

  return (
    <Card>
      <SectionHeader title="Clubs on the board" to="/clubs" linkLabel="All clubs" />
      {isLoading && (
        <div className="space-y-3 animate-pulse">
          {[1, 2].map(i => (
            <div key={i} className="flex gap-3 items-center">
              <div className="w-9 h-9 rounded-full bg-ink/5 flex-shrink-0" />
              <div className="h-3.5 bg-ink/5 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}
      {!isLoading && (!shown || shown.length === 0) && (
        <EmptyState
          title="No clubs yet"
          message="Be the first to pitch one."
          action={<Link to="/clubs" className="text-sm font-display font-semibold text-rust hover:underline">Browse clubs</Link>}
        />
      )}
      {shown && shown.length > 0 && (
        <ul className="divide-y divide-dashed divide-ink/10">
          {shown.map((c: Club) => (
            <li key={c.id}>
              <Link
                to={`/clubs/${c.id}`}
                className="flex items-center gap-3 py-2.5 group"
              >
                <Seal name={c.name} logoUrl={c.logo_url} size="sm" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-ink truncate group-hover:text-rust transition-colors">
                    {c.name}
                  </p>
                  {c.domain && (
                    <p className="text-xs text-ink/40 capitalize">{c.domain}</p>
                  )}
                </div>
                <span className="text-xs text-ink/30 flex-shrink-0">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

// ── Recent Notifications ───────────────────────────────────────────────────
function RecentNotifications() {
  const { data: notifications, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: getNotifications,
  })

  const recent = notifications?.slice(0, 4)
  const unread = notifications?.filter((n: Notification) => !n.is_read).length ?? 0

  return (
    <Card>
      <SectionHeader
        title={unread > 0 ? `Notifications · ${unread} new` : 'Notifications'}
        to="/notifications"
        linkLabel="See all"
      />
      {isLoading && (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="space-y-1.5">
              <div className="h-3.5 bg-ink/5 rounded w-3/4" />
              <div className="h-3 bg-ink/5 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}
      {!isLoading && (!recent || recent.length === 0) && (
        <EmptyState title="All quiet" message="Nothing new to report." />
      )}
      {recent && recent.length > 0 && (
        <ul className="divide-y divide-dashed divide-ink/10">
          {recent.map((n: Notification) => (
            <li key={n.id} className="py-2.5 flex items-start gap-2">
              <span className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${n.is_read ? 'bg-transparent' : 'bg-rust'}`} />
              <div className="flex-1 min-w-0">
                <p className={`text-sm truncate ${n.is_read ? 'text-ink/50' : 'text-ink font-medium'}`}>
                  {n.title}
                </p>
                <p className="text-xs text-ink/35 mt-0.5 font-mono">{timeAgo(n.created_at)}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

// ── Admin strip ───────────────────────────────────────────────────────────
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
    <div className="pin-card rounded-2xl border border-ink/5 shadow-pin p-5 pt-7 mb-6">
      <p className="stamp-label text-rust mb-3">Platform overview</p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Users',          value: s.total_users },
          { label: 'Active clubs',   value: s.active_clubs },
          { label: 'Upcoming events',value: s.upcoming_events },
          { label: 'Certificates',   value: s.total_certificates_issued },
        ].map(({ label, value }) => (
          <div key={label}>
            <p className="text-2xl font-display font-bold text-ink">{value.toLocaleString()}</p>
            <p className="text-xs text-ink/40 mt-0.5">{label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────
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
    <div className="min-h-screen bg-paper">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Greeting */}
        <div className="mb-6">
          {meLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-8 bg-ink/5 rounded w-1/3" />
              <div className="h-4 bg-ink/5 rounded w-1/4" />
            </div>
          ) : (
            <>
              <p className="stamp-label text-rust mb-1">{new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}</p>
              <h1 className="text-2xl sm:text-3xl font-display font-bold text-ink">
                {greeting}{me ? `, ${me.full_name.split(' ')[0]}` : ''}
              </h1>
            </>
          )}
        </div>

        {isAdmin && <AdminStrip />}

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <UpcomingEvents />
          <div className="space-y-5">
            <MyClubs />
            <RecentNotifications />
          </div>
        </div>

        {/* Quick links */}
        <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { to: '/clubs',         label: 'Browse clubs' },
            { to: '/events',        label: 'Find events' },
            { to: '/notifications', label: 'Notifications' },
            { to: '/profile',       label: 'Your profile' },
          ].map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="bg-white rounded-xl border border-ink/5 shadow-pin px-4 py-3 text-sm font-display font-semibold text-ink/60 hover:text-rust hover:border-rust/20 hover:shadow-pin-hover transition-all"
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
