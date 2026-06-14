import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMe, updateMe, type UserUpdate } from '../api/users'
import Navbar from '../components/Navbar'
import { Field, Input, Textarea } from '../components/FormField'
import Seal from '../components/Seal'
import Tag from '../components/Tag'

export default function Profile() {
  const qc = useQueryClient()

  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  })

  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<UserUpdate>({})
  const [saveError, setSaveError] = useState('')

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
      <div className="min-h-screen bg-paper">
        <Navbar />
        <div className="max-w-xl mx-auto px-4 sm:px-6 py-8 animate-pulse space-y-4">
          <div className="h-16 w-16 rounded-full bg-ink/5" />
          <div className="h-6 bg-ink/5 rounded w-1/3" />
          <div className="h-4 bg-ink/5 rounded w-1/2" />
        </div>
      </div>
    )
  }

  if (isError || !user) {
    return (
      <div className="min-h-screen bg-paper">
        <Navbar />
        <div className="text-center py-24 text-alert text-sm">Failed to load profile.</div>
      </div>
    )
  }

  const roleTone =
    user.role === 'college_admin' ? 'rust' :
    user.role === 'club_admin'    ? 'slate' :
    'neutral'

  return (
    <div className="min-h-screen bg-paper">
      <Navbar />
      <div className="max-w-xl mx-auto px-4 sm:px-6 py-8">
        <p className="stamp-label text-rust mb-1">Your details</p>
        <h1 className="text-2xl font-display font-bold text-ink mb-6">Profile</h1>

        <div className="pin-card rounded-2xl border border-ink/5 shadow-pin p-6 pt-8">
          {/* Avatar + identity */}
          <div className="flex items-center gap-4 mb-6">
            {user.profile_picture ? (
              <img
                src={user.profile_picture}
                alt={user.full_name}
                className="w-16 h-16 rounded-full object-cover ring-2 ring-white ring-offset-2 ring-offset-paper"
              />
            ) : (
              <Seal name={user.full_name} size="lg" />
            )}
            <div className="min-w-0">
              <h2 className="font-display font-bold text-lg text-ink truncate">{user.full_name}</h2>
              <p className="text-sm text-ink/50">{user.email}</p>
              <div className="mt-1.5">
                <Tag tone={roleTone}>{user.role.replace(/_/g, ' ')}</Tag>
              </div>
            </div>
          </div>

          {/* Editable fields */}
          {editing ? (
            <div className="space-y-4">
              <Field label="Full name">
                <Input
                  value={draft.full_name ?? ''}
                  onChange={(e) => setDraft((d) => ({ ...d, full_name: e.target.value }))}
                  placeholder="Jane Doe"
                />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Branch">
                  <Input
                    value={draft.branch ?? ''}
                    onChange={(e) => setDraft((d) => ({ ...d, branch: e.target.value }))}
                    placeholder="Computer Engg"
                  />
                </Field>
                <Field label="Year">
                  <Input
                    type="number"
                    min={1}
                    max={6}
                    value={draft.year != null ? String(draft.year) : ''}
                    onChange={(e) =>
                      setDraft((d) => ({ ...d, year: e.target.value ? parseInt(e.target.value, 10) : undefined }))
                    }
                    placeholder="2"
                  />
                </Field>
              </div>
              <Field label="Bio" hint="Tell people what you're about">
                <Textarea
                  value={draft.bio ?? ''}
                  onChange={(e) => setDraft((d) => ({ ...d, bio: e.target.value }))}
                  rows={3}
                  placeholder="Final year CE student, robotics enthusiast…"
                />
              </Field>
              <Field label="Skills" hint="Comma-separated">
                <Input
                  value={draft.skills ?? ''}
                  onChange={(e) => setDraft((d) => ({ ...d, skills: e.target.value }))}
                  placeholder="Python, CAD, Circuit design"
                />
              </Field>

              {saveError && (
                <p className="text-sm text-alert">{saveError}</p>
              )}

              <div className="flex gap-3 pt-1">
                <button
                  onClick={() => saveMut.mutate()}
                  disabled={saveMut.isPending}
                  className="px-5 py-2 rounded-lg text-sm font-display font-semibold bg-rust hover:bg-rust/90 disabled:opacity-50 text-white transition-colors"
                >
                  {saveMut.isPending ? 'Saving…' : 'Save changes'}
                </button>
                <button
                  onClick={() => {
                    setEditing(false)
                    setSaveError('')
                    setDraft({
                      full_name: user.full_name,
                      bio: user.bio ?? '',
                      skills: user.skills ?? '',
                      branch: user.branch ?? '',
                      year: user.year ?? undefined,
                    })
                  }}
                  disabled={saveMut.isPending}
                  className="px-5 py-2 rounded-lg text-sm font-display font-semibold border border-ink/15 text-ink hover:bg-ink/5 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <dl className="space-y-4">
              {[
                { label: 'Branch', value: user.branch },
                { label: 'Year', value: user.year != null ? `Year ${user.year}` : undefined },
                { label: 'Bio', value: user.bio },
                { label: 'Skills', value: user.skills },
              ].map(({ label, value }) => (
                <div key={label}>
                  <dt className="stamp-label text-ink/35 mb-1">{label}</dt>
                  <dd className="text-sm text-ink">
                    {value || <span className="text-ink/25 italic">Not set</span>}
                  </dd>
                </div>
              ))}

              <div className="pt-2">
                <button
                  onClick={() => setEditing(true)}
                  className="px-5 py-2 rounded-lg text-sm font-display font-semibold bg-ink hover:bg-ink/90 text-paper transition-colors"
                >
                  Edit profile
                </button>
              </div>
            </dl>
          )}
        </div>
      </div>
    </div>
  )
}
