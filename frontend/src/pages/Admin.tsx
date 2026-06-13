import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Navbar from '../components/Navbar'
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

type Tab = 'overview' | 'users' | 'clubs' | 'budget'

const ROLES = ['student', 'club_admin', 'faculty_advisor', 'college_admin']

// ── Stat card ──────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">{label}</p>
      <p className="text-3xl font-bold text-gray-800 mt-1">{value.toLocaleString()}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

// ── Overview tab ───────────────────────────────────────────────────────────────
function OverviewTab() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: getStats,
  })

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 animate-pulse">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError || !data) {
    return <p className="text-red-500 text-sm">Failed to load stats.</p>
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      <StatCard label="Total users" value={data.total_users} />
      <StatCard label="Total clubs" value={data.total_clubs} sub={`${data.suspended_clubs} suspended`} />
      <StatCard label="Active clubs" value={data.active_clubs} />
      <StatCard label="Total events" value={data.total_events} sub={`${data.upcoming_events} upcoming`} />
      <StatCard label="Total RSVPs" value={data.total_rsvps} />
      <StatCard label="Attendance records" value={data.total_attendance} />
      <StatCard label="Certificates issued" value={data.total_certificates_issued} />
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

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <label className="text-sm text-gray-500">Filter by role</label>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All roles</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>{r.replace('_', ' ')}</option>
          ))}
        </select>
      </div>

      {actionError && (
        <p className="mb-3 text-sm text-red-500">{actionError}</p>
      )}

      {isLoading && (
        <div className="space-y-2 animate-pulse">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-100 rounded-lg" />
          ))}
        </div>
      )}

      {isError && <p className="text-red-500 text-sm">Failed to load users.</p>}

      {users && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100">
                <th className="pb-2 pr-4">Name</th>
                <th className="pb-2 pr-4">Email</th>
                <th className="pb-2 pr-4">Role</th>
                <th className="pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u: AdminUser) => (
                <tr key={u.id} className="border-b border-gray-50 last:border-0">
                  <td className="py-3 pr-4 font-medium text-gray-700">{u.full_name}</td>
                  <td className="py-3 pr-4 text-gray-500">{u.email}</td>
                  <td className="py-3 pr-4">
                    <span
                      className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium ${
                        u.role === 'college_admin'
                          ? 'bg-purple-50 text-purple-600'
                          : u.role === 'club_admin'
                          ? 'bg-blue-50 text-blue-600'
                          : u.role === 'faculty_advisor'
                          ? 'bg-green-50 text-green-600'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {u.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3">
                    {changingId === u.id ? (
                      <div className="flex items-center gap-2">
                        <select
                          value={newRole}
                          onChange={(e) => setNewRole(e.target.value)}
                          className="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Pick role</option>
                          {ROLES.map((r) => (
                            <option key={r} value={r}>{r.replace('_', ' ')}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => newRole && roleMut.mutate({ id: u.id, role: newRole })}
                          disabled={!newRole || roleMut.isPending}
                          className="text-xs px-2 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
                        >
                          {roleMut.isPending ? '…' : 'Save'}
                        </button>
                        <button
                          onClick={() => { setChangingId(null); setActionError('') }}
                          className="text-xs text-gray-400 hover:text-gray-600"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => { setChangingId(u.id); setNewRole(u.role) }}
                        className="text-xs text-blue-500 hover:text-blue-700"
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
            <p className="text-center py-8 text-gray-400 text-sm">No users found.</p>
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
          <div key={i} className="h-12 bg-gray-100 rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError) return <p className="text-red-500 text-sm">Failed to load clubs.</p>

  return (
    <div>
      {actionError && <p className="mb-3 text-sm text-red-500">{actionError}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100">
              <th className="pb-2 pr-4">Club</th>
              <th className="pb-2 pr-4">Domain</th>
              <th className="pb-2 pr-4">Members</th>
              <th className="pb-2 pr-4">Status</th>
              <th className="pb-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {clubs?.map((c: AdminClub) => (
              <tr key={c.id} className="border-b border-gray-50 last:border-0">
                <td className="py-3 pr-4 font-medium text-gray-700">{c.name}</td>
                <td className="py-3 pr-4 text-gray-500">{c.domain ?? '—'}</td>
                <td className="py-3 pr-4 text-gray-500">{c.member_count}</td>
                <td className="py-3 pr-4">
                  {c.is_suspended ? (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-500 font-medium">
                      Suspended
                    </span>
                  ) : (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-600 font-medium">
                      Active
                    </span>
                  )}
                </td>
                <td className="py-3">
                  <button
                    onClick={() => suspendMut.mutate(c.id)}
                    disabled={suspendMut.isPending}
                    className={`text-xs px-3 py-1 rounded-lg font-medium transition-colors disabled:opacity-50 ${
                      c.is_suspended
                        ? 'bg-green-50 text-green-700 hover:bg-green-100'
                        : 'bg-red-50 text-red-600 hover:bg-red-100'
                    }`}
                  >
                    {c.is_suspended ? 'Reinstate' : 'Suspend'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {clubs?.length === 0 && (
          <p className="text-center py-8 text-gray-400 text-sm">No clubs found.</p>
        )}
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
          <div key={i} className="h-10 bg-gray-100 rounded-lg" />
        ))}
      </div>
    )
  }

  if (isError) return <p className="text-red-500 text-sm">Failed to load budget report.</p>

  const total_allocated = data?.reduce((s, r) => s + r.total_allocated, 0) ?? 0
  const total_spent = data?.reduce((s, r) => s + r.total_spent, 0) ?? 0

  return (
    <div>
      <div className="flex gap-6 mb-5 text-sm">
        <span className="text-gray-500">
          Total allocated: <span className="font-semibold text-gray-700">₹{total_allocated.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
        </span>
        <span className="text-gray-500">
          Total spent: <span className="font-semibold text-gray-700">₹{total_spent.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-400 uppercase tracking-wide border-b border-gray-100">
              <th className="pb-2 pr-4">Club</th>
              <th className="pb-2 pr-4">Allocated (₹)</th>
              <th className="pb-2 pr-4">Spent (₹)</th>
              <th className="pb-2">Remaining (₹)</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((r: BudgetReportItem) => {
              const remaining = r.total_allocated - r.total_spent
              const overBudget = remaining < 0
              return (
                <tr key={r.club_id} className="border-b border-gray-50 last:border-0">
                  <td className="py-3 pr-4 font-medium text-gray-700">{r.club_name}</td>
                  <td className="py-3 pr-4 text-gray-600">
                    {r.total_allocated.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 pr-4 text-gray-600">
                    {r.total_spent.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className={`py-3 font-medium ${overBudget ? 'text-red-500' : 'text-green-600'}`}>
                    {overBudget ? '−' : ''}
                    {Math.abs(remaining).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {data?.length === 0 && (
          <p className="text-center py-8 text-gray-400 text-sm">No budget data yet.</p>
        )}
      </div>
    </div>
  )
}

// ── Main Admin page ────────────────────────────────────────────────────────────
const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'users',    label: 'Users' },
  { id: 'clubs',    label: 'Clubs' },
  { id: 'budget',   label: 'Budget' },
]

export default function Admin() {
  const [tab, setTab] = useState<Tab>('overview')

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">Admin Panel</h1>
        <p className="text-sm text-gray-400 mb-6">Platform management — college admin only</p>

        {/* Tab bar */}
        <div className="flex gap-1 mb-6 bg-white border border-gray-100 rounded-xl p-1 w-fit shadow-sm">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                tab === id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          {tab === 'overview' && <OverviewTab />}
          {tab === 'users'    && <UsersTab />}
          {tab === 'clubs'    && <ClubsTab />}
          {tab === 'budget'   && <BudgetTab />}
        </div>
      </div>
    </div>
  )
}
