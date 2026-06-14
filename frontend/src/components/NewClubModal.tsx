
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Modal from './Modal'
import { Field, Input, Textarea, Select } from './FormField'
import { createClub, type ClubCreatePayload } from '../api/clubs'
import { applyForNewClub, type NewClubApplicationPayload } from '../api/club_applications'

const DOMAINS = ['technical', 'cultural', 'sports', 'social', 'academic']

interface NewClubModalProps {
  open: boolean
  onClose: () => void
  isAdmin: boolean
}

export default function NewClubModal({ open, onClose, isAdmin }: NewClubModalProps) {
  const qc = useQueryClient()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [domain, setDomain] = useState('')
  const [joinType, setJoinType] = useState<'open' | 'invite_only'>('open')
  const [advisorEmail, setAdvisorEmail] = useState('')

  function reset() {
    setName('')
    setDescription('')
    setDomain('')
    setJoinType('open')
    setAdvisorEmail('')
  }

  function handleClose() {
    reset()
    createMut.reset()
    applyMut.reset()
    onClose()
  }

  // college_admin → registers the club immediately
  const createMut = useMutation({
    mutationFn: (payload: ClubCreatePayload) => createClub(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['clubs'] })
      handleClose()
    },
  })

  // student → submits an application for college_admin to review
  const applyMut = useMutation({
    mutationFn: (payload: NewClubApplicationPayload) => applyForNewClub(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['club-applications'] })
    },
  })

  function handleSubmit() {
    if (!name.trim()) return

    if (isAdmin) {
      createMut.mutate({
        name: name.trim(),
        description: description.trim() || undefined,
        domain: domain || undefined,
        join_type: joinType,
      })
    } else {
      applyMut.mutate({
        club_name: name.trim(),
        description: description.trim() || undefined,
        domain: domain || undefined,
        faculty_advisor_email: advisorEmail.trim() || undefined,
      })
    }
  }

  const pending = createMut.isPending || applyMut.isPending
  const error =
    (createMut.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
    (applyMut.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail

  // After a successful application, show a confirmation instead of the form
  if (applyMut.isSuccess) {
    return (
      <Modal open={open} onClose={handleClose} eyebrow="Application sent" title="On its way to the board">
        <div className="text-center py-4">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-pine/10 flex items-center justify-center">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2D6A4F" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6L9 17l-5-5" />
            </svg>
          </div>
          <p className="text-sm text-ink/70">
            Your application for <span className="font-semibold text-ink">{name}</span> has been
            sent to the college admin for review. You'll get a notification once it's decided.
          </p>
          <button
            onClick={handleClose}
            className="mt-5 px-4 py-2 rounded-lg bg-ink text-paper text-sm font-medium font-display hover:bg-ink/90 transition-colors"
          >
            Done
          </button>
        </div>
      </Modal>
    )
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      eyebrow={isAdmin ? 'Register a club' : 'Apply for a new club'}
      title={isAdmin ? 'Add a club to the board' : 'Pitch a new club'}
    >
      {!isAdmin && (
        <p className="text-sm text-ink/50 mb-4 -mt-1">
          Submit the details below and the college admin will review your pitch. You'll be
          notified either way.
        </p>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-alert/10 text-alert px-3 py-2 text-sm">{error}</div>
      )}

      <div className="space-y-4">
        <Field label="Club name">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Robotics Society"
            autoFocus
          />
        </Field>

        <Field label="Description" hint="What does this club do? Who is it for?">
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="Building autonomous bots, weekly workshops, inter-college competitions…"
          />
        </Field>

        <Field label="Domain">
          <Select value={domain} onChange={(e) => setDomain(e.target.value)}>
            <option value="">Select a domain</option>
            {DOMAINS.map((d) => (
              <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
            ))}
          </Select>
        </Field>

        {isAdmin ? (
          <Field label="Who can join?">
            <Select value={joinType} onChange={(e) => setJoinType(e.target.value as 'open' | 'invite_only')}>
              <option value="open">Open — anyone can join instantly</option>
              <option value="invite_only">Invite only — requests need approval</option>
            </Select>
          </Field>
        ) : (
          <Field label="Faculty advisor email" hint="Optional — helps the admin verify your pitch">
            <Input
              type="email"
              value={advisorEmail}
              onChange={(e) => setAdvisorEmail(e.target.value)}
              placeholder="advisor@college.edu"
            />
          </Field>
        )}

        <button
          onClick={handleSubmit}
          disabled={pending || !name.trim()}
          className="w-full bg-rust hover:bg-rust/90 disabled:opacity-50 text-white font-display font-semibold rounded-lg py-2.5 text-sm transition-colors"
        >
          {pending
            ? 'Sending…'
            : isAdmin
            ? 'Add club to the board'
            : 'Send application'}
        </button>
      </div>
    </Modal>
  )
}
