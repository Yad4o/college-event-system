import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMe, updateMe, type UserUpdate } from '../api/users'
import Navbar from '../components/Navbar'

function Field({
  label,
  value,
  editing,
  type = 'text',
  onChange,
}: {
  label: string
  value: string
  editing: boolean
  type?: string
  onChange: (v: string) => void
}) {
  return (
    <div>
      <dt className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
        {label}
      </dt>
      {editing ? (
        type === 'textarea' ? (
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            rows={3}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        ) : (
          <input
            type={type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        )
      ) : (
        <dd className="text-sm text-gray-700">
          {value || <span className="text-gray-300 italic">Not set</span>}
        </dd>
      )}
    </div>
  )
}

export default function Profile() {
  const qc = useQueryClient()

  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  })

  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<UserUpdate>({})
  const [saveError, setSaveError] = useState('')

  // Sync draft when user data loads
  useEffect(() => {
    if (user) {
      setDraft({
        full_name: user.full_name,
        bio: user.bio ?? '',
        skills: user.skills ?? '',
        branch: user.branch ?? '',
        year: user.year ?? undefined,
      })
    }
  }, [user])

  const saveMut = useMutation({
    mutationFn: () =>
      updateMe({
        full_name: draft.full_name || undefined,
        bio: draft.bio || undefined,
        skills: draft.skills || undefined,
        branch: draft.branch || undefined,
        year: draft.year ?? undefined,
      }),
    onSuccess: (updated) => {
      qc.setQueryData(['me'], updated)
      setEditing(false)
      setSaveError('')
    },
    onError: () => setSaveError('Failed to save changes. Please try again.'),
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-xl mx-auto px-6 py-8 animate-pulse space-y-4">
          <div className="h-16 w-16 rounded-full bg-gray-100" />
          <div className="h-6 bg-gray-100 rounded w-1/3" />
          <div className="h-4 bg-gray-100 rounded w-1/2" />
        </div>
      </div>
    )
  }

  if (isError || !user) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="text-center py-24 text-red-500">Failed to load profile.</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-xl mx-auto px-6 py-8">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          {/* Avatar + name header */}
          <div className="flex items-center gap-4 mb-6">
            {user.profile_picture ? (
              <img
                src={user.profile_picture}
                alt={user.full_name}
                className="w-16 h-16 rounded-full object-cover"
              />
            ) : (
              <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-2xl font-bold text-blue-600">
                  {user.full_name.charAt(0).toUpperCase()}
                </span>
              </div>
            )}
            <div>
              <h1 className="text-xl font-bold text-gray-800">{user.full_name}</h1>
              <p className="text-sm text-gray-500">{user.email}</p>
              <span
                className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full font-medium ${
                  user.role === 'college_admin'
                    ? 'bg-purple-50 text-purple-600'
                    : user.role === 'club_admin'
                    ? 'bg-blue-50 text-blue-600'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {user.role.replace('_', ' ')}
              </span>
            </div>
          </div>

          {/* Editable fields */}
          <dl className="space-y-4">
            <Field
              label="Full name"
              value={draft.full_name ?? ''}
              editing={editing}
              onChange={(v) => setDraft((d) => ({ ...d, full_name: v }))}
            />
            <Field
              label="Branch"
              value={draft.branch ?? ''}
              editing={editing}
              onChange={(v) => setDraft((d) => ({ ...d, branch: v }))}
            />
            <Field
              label="Year"
              value={draft.year != null ? String(draft.year) : ''}
              editing={editing}
              type="number"
              onChange={(v) =>
                setDraft((d) => ({ ...d, year: v ? parseInt(v, 10) : undefined }))
              }
            />
            <Field
              label="Bio"
              value={draft.bio ?? ''}
              editing={editing}
              type="textarea"
              onChange={(v) => setDraft((d) => ({ ...d, bio: v }))}
            />
            <Field
              label="Skills"
              value={draft.skills ?? ''}
              editing={editing}
              onChange={(v) => setDraft((d) => ({ ...d, skills: v }))}
            />
          </dl>

          {saveError && (
            <p className="mt-4 text-sm text-red-500">{saveError}</p>
          )}

          {/* Action buttons */}
          <div className="mt-6 flex gap-3">
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors"
              >
                Edit profile
              </button>
            ) : (
              <>
                <button
                  onClick={() => saveMut.mutate()}
                  disabled={saveMut.isPending}
                  className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white transition-colors"
                >
                  {saveMut.isPending ? 'Saving…' : 'Save'}
                </button>
                <button
                  onClick={() => {
                    setEditing(false)
                    setSaveError('')
                    // Reset draft back to server data
                    setDraft({
                      full_name: user.full_name,
                      bio: user.bio ?? '',
                      skills: user.skills ?? '',
                      branch: user.branch ?? '',
                      year: user.year ?? undefined,
                    })
                  }}
                  disabled={saveMut.isPending}
                  className="px-4 py-2 rounded-lg text-sm font-medium border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
