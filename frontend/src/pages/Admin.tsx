import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Navbar from '../components/Navbar'
import EmptyState from '../components/EmptyState'
import Tag from '../components/Tag'
import {
  getStats,
  getAdminUsers,
  getAdminClubs,
  getBudgetReport,
  changeUserRole,
  toggleClubSuspension,
  type AdminUser,
  type AdminClub,
  type BudgetReportItem,
} from '../api/admin'
import {
  getClubApplications,
  reviewClubApplication,
  type NewClubApplication,
} from '../api/club_applications'

type Tab = 'overview' | 'applications' | 'users' | 'clubs' | 'budget' | 'events'

const ROLES = ['student', 'club_admin', 'faculty_advisor', 'college_admin']

// ── shared primitives ────────────────────────────────────────────────────────

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="pin-card rounded-2xl border border-ink/5 shadow-pin p-6 pt-7">
      {children}
    </div>
  )
}

function StatTile({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <div className="bg-paper rounded-xl border border-ink/5 p-4">
      <p className="stamp-label text-ink/35 mb-1">{label}</p>
      <p className="text-3xl font-display font-bold text-ink leading-none">{value.toLocaleString()}</p>
      {sub && <p className="text-xs text-ink/40 mt-1 font-mono">{sub}</p>}
    </div>
  )
}

// ── Overview tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: getStats,
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 animate-pulse">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="h-24 bg-ink/5 rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError || !data) {
    return <EmptyState tone="error" title="Failed to load stats" />
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      <StatTile label="Total users"        value={data.total_users} />
      <StatTile label="Total clubs"        value={data.total_clubs} sub={`${data.suspended_clubs} suspended`} />
      <StatTile label="Active clubs"       value={data.active_clubs} />
      <StatTile label="Total events"       value={data.total_events} sub={`${data.upcoming_events} upcoming`} />
      <StatTile label="Total RSVPs"        value={data.total_rsvps} />
      <StatTile label="Attendance records" value={data.total_attendance} />
      <StatTile label="Certificates"       value={data.total_certificates_issued} />
    </div>
  )
}

// ── Club Applications tab ────────────────────────────────────────────────────

function ApplicationsTab() {
  const qc = useQueryClient()
  const [filter, setFilter] = useState<'pending' | 'approved' | 'rejected'>('pending')
  const [remarks, setRemarks] = useState<Record<number, string>>({})
  const [actionError, setActionError] = useState('')

  const { data: apps, isLoading, isError } = useQuery({
    queryKey: ['club-applications', filter],
    queryFn: () => getClubApplications(filter),
  })

  const reviewMut = useMutation({
    mutationFn: ({ id, decision }: { id: number; decision: 'approved' | 'rejected' }) =>
      reviewClubApplication(id, decision, remarks[id]),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['club-applications'] })
      qc.invalidateQueries({ queryKey: ['clubs'] })
      setActionError('')
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to process application.'
      setActionError(detail)
    },
  })

  return (
    <div>
      {/* Filter pills */}
      <div className="flex gap-2 mb-5">
        {(['pending', 'approved', 'rejected'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`stamp-label px-3 py-1.5 rounded-full border transition-colors ${
              filter === s
                ? 'bg-ink text-paper border-ink'
                : 'bg-white text-ink/50 border-ink/10 hover:border-ink/30'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {actionError && (
        <p className="mb-4 text-sm text-alert">{actionError}</p>
      )}

      {isLoading && (
        <div className="space-y-3 animate-pulse">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-24 bg-ink/5 rounded-xl" />
          ))}
        </div>
      )}

      {isError && (
        <EmptyState tone="error" title="Failed to load applications" />
      )}

      {!isLoading && !isError && (!apps || apps.length === 0) && (
        <EmptyState
          title={`No ${filter} applications`}
          message={
            filter === 'pending'
              ? 'No new club pitches waiting for review.'
              : `No applications have been ${filter} yet.`
          }
          icon={
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
          }
        />
      )}

      {apps && apps.length > 0 && (
        <div className="space-y-4">
          {apps.map((app: NewClubApplication) => (
            <div key={app.id} className="bg-paper rounded-xl border border-ink/8 p-4">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <h3 className="font-display font-semibold text-ink">{app.club_name}</h3>
                    {app.domain && <Tag tone="neutral">{app.domain}</Tag>}
                    <Tag
                      tone={
                        app.status === 'pending'  ? 'gold'  :
                        app.status === 'approved' ? 'pine'  : 'alert'
                      }
                    >
                      {app.status}
                    </Tag>
                  </div>
                  {app.description && (
                    <p className="text-sm text-ink/60 mt-1 leading-relaxed">{app.description}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-3 text-xs text-ink/40 font-mono">
                    <span>Applicant #{app.applicant_id}</span>
                    {app.faculty_advisor_email && (
                      <span>Advisor: {app.faculty_advisor_email}</span>
                    )}
                    <span>{new Date(app.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                  </div>
                  {app.admin_remarks && (
                    <p className="mt-2 text-xs text-ink/50 italic">Remarks: {app.admin_remarks}</p>
                  )}
                </div>
              </div>

              {/* Actions for pending only */}
              {app.status === 'pending' && (
                <div className="mt-4 pt-3 border-t border-dashed border-ink/8 space-y-2">
                  <input
                    type="text"
                    placeholder="Optional remarks (visible to applicant)"
                    value={remarks[app.id] ?? ''}
                    onChange={(e) =>
                      setRemarks((r) => ({ ...r, [app.id]: e.target.value }))
                    }
                    className="w-full bg-white border border-ink/10 rounded-lg px-3 py-2 text-sm text-ink placeholder:text-ink/30 focus:outline-none focus:ring-2 focus:ring-rust/40 focus:border-rust transition-colors"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => reviewMut.mutate({ id: app.id, decision: 'approved' })}
                      disabled={reviewMut.isPending}
                      className="flex-1 py-2 rounded-lg text-sm font-display font-semibold bg-pine hover:bg-pine/90 disabled:opacity-50 text-white transition-colors"
                    >
                      Approve & create club
                    </button>
                    <button
                      onClick={() => reviewMut.mutate({ id: app.id, decision: 'rejected' })}
                      disabled={reviewMut.isPending}
                      className="flex-1 py-2 rounded-lg text-sm font-display font-semibold border border-alert/30 text-alert hover:bg-alert/5 disabled:opacity-50 transition-colors"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Users tab ─────────────────────────────────────────────────────────────────

function UsersTab() {
  const qc = useQueryClient()
  const [roleFilter, setRoleFilter] = useState('')
  const [changingId, setChangingId] = useState<number | null>(null)
  const [newRole, setNewRole] = useState('')
  const [actionError, setActionError] = useState('')

  const { data: users, isLoading, isError } = useQuery({
    queryKey: ['admin-users', roleFilter],
    queryFn: () => getAdminUsers(roleFilter ? { role: roleFilter } : {}),
  })

  const roleMut = useMutation({
    mutationFn: ({ id, role }: { id: number; role: string }) => changeUserRole(id, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] })
      setChangingId(null)
      setNewRole('')
      setActionError('')
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to change role.'
      setActionError(detail)
    },
  })

  const roleTagTone = (role: string) =>
    role === 'college_admin'  ? 'rust' :
    role === 'club_admin'     ? 'slate' :
    role === 'faculty_advisor'? 'pine' : 'neutral'

  return (
    <div>
      <div className="flex items-center gap-3 mb-5">
        <span className="text-sm text-ink/50">Filter:</span>
        <div className="flex gap-2 flex-wrap">
          {(['', ...ROLES] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRoleFilter(r as string)}
              className={`stamp-label px-3 py-1 rounded-full border transition-colors ${
                roleFilter === r
                  ? 'bg-ink text-paper border-ink'
                  : 'bg-white text-ink/45 border-ink/10 hover:border-ink/25'
              }`}
            >
              {r ? r.replace(/_/g, ' ') : 'All'}
            </button>
          ))}
        </div>
      </div>

      {actionError && <p className="mb-3 text-sm text-alert">{actionError}</p>}

      {isLoading && (
        <div className="space-y-2 animate-pulse">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-ink/5 rounded-lg" />
          ))}
        </div>
      )}

      {isError && <EmptyState tone="error" title="Failed to load users" />}

      {users && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-dashed border-ink/10">
                <th className="pb-2 pr-4 stamp-label text-ink/35">Name</th>
                <th className="pb-2 pr-4 stamp-label text-ink/35">Email</th>
                <th className="pb-2 pr-4 stamp-label text-ink/35">Role</th>
                <th className="pb-2 stamp-label text-ink/35">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u: AdminUser) => (
                <tr key={u.id} className="border-b border-dashed border-ink/5 last:border-0">
                  <td className="py-3 pr-4 font-medium text-ink">{u.full_name}</td>
                  <td className="py-3 pr-4 text-ink/50 font-mono text-xs">{u.email}</td>
                  <td className="py-3 pr-4">
                    <Tag tone={roleTagTone(u.role)}>{u.role.replace(/_/g, ' ')}</Tag>
                  </td>
                  <td className="py-3">
                    {changingId === u.id ? (
                      <div className="flex items-center gap-2">
                        <select
                          value={newRole}
                          onChange={(e) => setNewRole(e.target.value)}
                          className="border border-ink/10 rounded-lg px-2 py-1 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-rust/40"
                        >
                          <option value="">Pick role</option>
                          {ROLES.map((r) => (
                            <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => newRole && roleMut.mutate({ id: u.id, role: newRole })}
                          disabled={!newRole || roleMut.isPending}
                          className="text-xs px-2.5 py-1 rounded-lg bg-rust text-white disabled:opacity-50 font-display font-semibold"
                        >
                          {roleMut.isPending ? '…' : 'Save'}
                        </button>
                        <button
                          onClick={() => { setChangingId(null); setActionError('') }}
                          className="text-xs text-ink/35 hover:text-ink"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => { setChangingId(u.id); setNewRole(u.role) }}
                        className="text-xs font-display font-semibold text-ink/35 hover:text-rust transition-colors"
                      >
                        Change role
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {users.length === 0 && (
            <EmptyState title="No users found" />
          )}
        </div>
      )}
    </div>
  )
}

// ── Clubs tab ─────────────────────────────────────────────────────────────────

function ClubsTab() {
  const qc = useQueryClient()
  const [actionError, setActionError] = useState('')

  const { data: clubs, isLoading, isError } = useQuery({
    queryKey: ['admin-clubs'],
    queryFn: getAdminClubs,
  })

  const suspendMut = useMutation({
    mutationFn: (clubId: number) => toggleClubSuspension(clubId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-clubs'] })
      setActionError('')
    },
    onError: () => setActionError('Failed to toggle suspension.'),
  })

  if (isLoading) {
    return (
      <div className="space-y-2 animate-pulse">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-12 bg-ink/5 rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError) return <EmptyState tone="error" title="Failed to load clubs" />

  return (
    <div>
      {actionError && <p className="mb-3 text-sm text-alert">{actionError}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b border-dashed border-ink/10">
              <th className="pb-2 pr-4 stamp-label text-ink/35">Club</th>
              <th className="pb-2 pr-4 stamp-label text-ink/35">Domain</th>
              <th className="pb-2 pr-4 stamp-label text-ink/35">Members</th>
              <th className="pb-2 pr-4 stamp-label text-ink/35">Status</th>
              <th className="pb-2 stamp-label text-ink/35">Action</th>
            </tr>
          </thead>
          <tbody>
            {clubs?.map((c: AdminClub) => (
              <tr key={c.id} className="border-b border-dashed border-ink/5 last:border-0">
                <td className="py-3 pr-4 font-medium text-ink">{c.name}</td>
                <td className="py-3 pr-4 text-ink/50">{c.domain ?? '—'}</td>
                <td className="py-3 pr-4 text-ink/50 font-mono">{c.member_count}</td>
                <td className="py-3 pr-4">
                  <Tag tone={c.is_suspended ? 'alert' : 'pine'}>
                    {c.is_suspended ? 'Suspended' : 'Active'}
                  </Tag>
                </td>
                <td className="py-3">
                  <button
                    onClick={() => suspendMut.mutate(c.id)}
                    disabled={suspendMut.isPending}
                    className={`text-xs font-display font-semibold px-3 py-1.5 rounded-full border disabled:opacity-50 transition-colors ${
                      c.is_suspended
                        ? 'border-pine/30 text-pine hover:bg-pine/5'
                        : 'border-alert/30 text-alert hover:bg-alert/5'
                    }`}
                  >
                    {c.is_suspended ? 'Reinstate' : 'Suspend'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {clubs?.length === 0 && <EmptyState title="No clubs found" />}
      </div>
    </div>
  )
}

// ── Budget tab ─────────────────────────────────────────────────────────────────

function BudgetTab() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin-budget'],
    queryFn: getBudgetReport,
  })

  if (isLoading) {
    return (
      <div className="space-y-2 animate-pulse">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-10 bg-ink/5 rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError) return <EmptyState tone="error" title="Failed to load budget report" />

  const totalAllocated = data?.reduce((s, r) => s + r.total_allocated, 0) ?? 0
  const totalSpent     = data?.reduce((s, r) => s + r.total_spent, 0) ?? 0

  const fmt = (n: number) =>
    n.toLocaleString('en-IN', { minimumFractionDigits: 2 })

  return (
    <div>
      <div className="flex flex-wrap gap-6 mb-5 pb-4 border-b border-dashed border-ink/10">
        <div>
          <p className="stamp-label text-ink/35 mb-1">Total allocated</p>
          <p className="font-display font-bold text-xl text-ink">₹{fmt(totalAllocated)}</p>
        </div>
        <div>
          <p className="stamp-label text-ink/35 mb-1">Total spent</p>
          <p className="font-display font-bold text-xl text-ink">₹{fmt(totalSpent)}</p>
        </div>
        <div>
          <p className="stamp-label text-ink/35 mb-1">Remaining</p>
          <p className={`font-display font-bold text-xl ${totalAllocated - totalSpent < 0 ? 'text-alert' : 'text-pine'}`}>
            ₹{fmt(Math.abs(totalAllocated - totalSpent))}
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b border-dashed border-ink/10">
              <th className="pb-2 pr-4 stamp-label text-ink/35">Club</th>
              <th className="pb-2 pr-4 stamp-label text-ink/35">Allocated (₹)</th>
              <th className="pb-2 pr-4 stamp-label text-ink/35">Spent (₹)</th>
              <th className="pb-2 stamp-label text-ink/35">Remaining (₹)</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((r: BudgetReportItem) => {
              const remaining = r.total_allocated - r.total_spent
              return (
                <tr key={r.club_id} className="border-b border-dashed border-ink/5 last:border-0">
                  <td className="py-3 pr-4 font-medium text-ink">{r.club_name}</td>
                  <td className="py-3 pr-4 text-ink/60 font-mono">{fmt(r.total_allocated)}</td>
                  <td className="py-3 pr-4 text-ink/60 font-mono">{fmt(r.total_spent)}</td>
                  <td className={`py-3 font-mono font-semibold ${remaining < 0 ? 'text-alert' : 'text-pine'}`}>
                    {remaining < 0 ? '−' : ''}{fmt(Math.abs(remaining))}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {data?.length === 0 && <EmptyState title="No budget data yet" />}
      </div>
    </div>
  )
}

// ── Events tab (Approvals) ────────────────────────────────────────────────────────
import { getEvents, approveEvent, rejectEvent, type Event } from '../api/events'

function EventsTab() {
  const qc = useQueryClient()
  const [actionError, setActionError] = useState('')

  const { data: events, isLoading, isError } = useQuery({
    queryKey: ['admin-events'],
    queryFn: () => getEvents({ limit: 100 }),
  })

  const pendingEvents = events?.filter(e => !e.is_approved) ?? []

  const approveMut = useMutation({
    mutationFn: (eventId: number) => approveEvent(eventId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-events'] })
      setActionError('')
    },
    onError: () => setActionError('Failed to approve event.'),
  })

  const rejectMut = useMutation({
    mutationFn: (eventId: number) => rejectEvent(eventId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-events'] })
      setActionError('')
    },
    onError: () => setActionError('Failed to reject event.'),
  })

  if (isLoading) {
    return (
      <div className="space-y-2 animate-pulse">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-12 bg-ink/5 rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError) return <EmptyState tone="error" title="Failed to load events" />

  return (
    <div>
      {actionError && <p className="mb-3 text-sm text-alert">{actionError}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left border-b border-dashed border-ink/10">
              <th className="pb-2 pr-4 stamp-label text-ink/35">Event</th>
              <th className="pb-2 pr-4 stamp-label text-ink/35">Club ID</th>
              <th className="pb-2 pr-4 stamp-label text-ink/35">Start</th>
              <th className="pb-2 stamp-label text-ink/35">Actions</th>
            </tr>
          </thead>
          <tbody>
            {pendingEvents.map((ev: Event) => (
              <tr key={ev.id} className="border-b border-dashed border-ink/5 last:border-0">
                <td className="py-3 pr-4 font-medium text-ink">{ev.title}</td>
                <td className="py-3 pr-4 text-ink/50 font-mono">#{ev.club_id}</td>
                <td className="py-3 pr-4 text-ink/50 font-mono">
                  {new Date(ev.start_at).toLocaleString()}
                </td>
                <td className="py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => approveMut.mutate(ev.id)}
                      disabled={approveMut.isPending}
                      className="text-xs px-3 py-1.5 rounded bg-pine text-white font-display font-semibold hover:bg-pine/90 disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => rejectMut.mutate(ev.id)}
                      disabled={rejectMut.isPending}
                      className="text-xs px-3 py-1.5 rounded border border-alert/30 text-alert font-display font-semibold hover:bg-alert/5 disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {pendingEvents.length === 0 && <EmptyState title="No pending events" />}
      </div>
    </div>
  )
}

// ── Main Admin page ────────────────────────────────────────────────────────────

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview',     label: 'Overview' },
  { id: 'applications', label: 'Applications' },
  { id: 'users',        label: 'Users' },
  { id: 'clubs',        label: 'Clubs' },
  { id: 'budget',       label: 'Budget' },
  { id: 'events',       label: 'Events' },
]

export default function Admin() {
  const [tab, setTab] = useState<Tab>('overview')

  // Badge on Applications tab — show count of pending
  const { data: pending } = useQuery({
    queryKey: ['club-applications', 'pending'],
    queryFn: () => getClubApplications('pending'),
    refetchInterval: 60_000,
  })
  const pendingCount = pending?.length ?? 0

  return (
    <div className="min-h-screen board-bg">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <p className="stamp-label text-rust mb-1">Platform control</p>
        <h1 className="text-2xl font-display font-bold text-ink mb-6">Admin Panel</h1>

        {/* Tab bar */}
        <div className="flex gap-1 mb-6 overflow-x-auto pb-1">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`relative flex-shrink-0 px-4 py-2 rounded-lg text-sm font-display font-semibold transition-colors ${
                tab === id
                  ? 'bg-ink text-paper'
                  : 'text-ink/50 hover:text-ink hover:bg-ink/5'
              }`}
            >
              {label}
              {id === 'applications' && pendingCount > 0 && (
                <span className="absolute -top-1 -right-1 min-w-[16px] h-4 flex items-center justify-center rounded-full bg-rust text-white text-[10px] font-bold px-1 leading-none font-mono">
                  {pendingCount}
                </span>
              )}
            </button>
          ))}
        </div>

        <Card>
          {tab === 'overview'     && <OverviewTab />}
          {tab === 'applications' && <ApplicationsTab />}
          {tab === 'users'        && <UsersTab />}
          {tab === 'clubs'        && <ClubsTab />}
          {tab === 'budget'       && <BudgetTab />}
          {tab === 'events'       && <EventsTab />}
        </Card>
      </div>
    </div>
  )
}
