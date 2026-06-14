
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getJoinRequests, decideJoinRequest } from '../api/clubs'

export default function JoinRequestsPanel({ clubId }: { clubId: number }) {
  const qc = useQueryClient()

  const { data: requests, isLoading, isError } = useQuery({
    queryKey: ['join-requests', clubId],
    queryFn: () => getJoinRequests(clubId),
    retry: false,
  })

  const decideMut = useMutation({
    mutationFn: ({ requestId, decision }: { requestId: number; decision: 'approved' | 'rejected' }) =>
      decideJoinRequest(clubId, requestId, decision),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['join-requests', clubId] })
      qc.invalidateQueries({ queryKey: ['club', clubId] })
    },
  })

  // 403 (not the president) → silently render nothing, this panel is admin-only
  if (isError || (!isLoading && !requests)) return null

  const pending = requests?.filter((r) => r.status === 'pending') ?? []

  if (!isLoading && pending.length === 0) return null

  return (
    <div className="pin-card rounded-2xl border border-ink/5 shadow-pin p-5 pt-7 mb-6">
      <p className="stamp-label text-rust mb-3">Join requests</p>

      {isLoading && (
        <div className="space-y-2 animate-pulse">
          {[1, 2].map((i) => <div key={i} className="h-10 bg-ink/5 rounded-lg" />)}
        </div>
      )}

      {!isLoading && (
        <ul className="space-y-2">
          {pending.map((r) => (
            <li key={r.id} className="flex items-center justify-between gap-3 bg-paper rounded-lg px-3 py-2">
              <div>
                <p className="text-sm font-medium text-ink">Applicant #{r.applicant_id}</p>
                <p className="text-xs text-ink/40 font-mono">
                  {new Date(r.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => decideMut.mutate({ requestId: r.id, decision: 'approved' })}
                  disabled={decideMut.isPending}
                  className="text-xs font-display font-semibold px-3 py-1.5 rounded-full bg-pine text-white hover:bg-pine/90 disabled:opacity-50 transition-colors"
                >
                  Approve
                </button>
                <button
                  onClick={() => decideMut.mutate({ requestId: r.id, decision: 'rejected' })}
                  disabled={decideMut.isPending}
                  className="text-xs font-display font-semibold px-3 py-1.5 rounded-full bg-ink/5 text-ink/60 hover:bg-ink/10 disabled:opacity-50 transition-colors"
                >
                  Decline
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
