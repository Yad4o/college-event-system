
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Modal from './Modal'
import { Field, Input, Textarea, Select } from './FormField'
import { createEvent, type EventCreatePayload } from '../api/events'

interface NewEventModalProps {
  open: boolean
  onClose: () => void
  clubId: number
  clubName: string
}

const EVENT_TYPES: { value: EventCreatePayload['event_type']; label: string; hint: string }[] = [
  { value: 'open',        label: 'Open to everyone',  hint: 'Any student can RSVP' },
  { value: 'club_only',   label: 'Club members only', hint: 'Only members of this club can RSVP' },
  { value: 'invite_only', label: 'Invite only',       hint: 'For invited attendees only' },
]

function toLocalInputValue(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export default function NewEventModal({ open, onClose, clubId, clubName }: NewEventModalProps) {
  const qc = useQueryClient()

  const defaultStart = new Date(Date.now() + 24 * 60 * 60 * 1000) // tomorrow, same time
  defaultStart.setMinutes(0)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [venue, setVenue] = useState('')
  const [eventType, setEventType] = useState<EventCreatePayload['event_type']>('open')
  const [startAt, setStartAt] = useState(toLocalInputValue(defaultStart))
  const [endAt, setEndAt] = useState('')
  const [seatLimit, setSeatLimit] = useState('')
  const [tagsInput, setTagsInput] = useState('')

  function reset() {
    setTitle('')
    setDescription('')
    setVenue('')
    setEventType('open')
    setStartAt(toLocalInputValue(defaultStart))
    setEndAt('')
    setSeatLimit('')
    setTagsInput('')
    mutation.reset()
  }

  function handleClose() {
    reset()
    onClose()
  }

  const mutation = useMutation({
    mutationFn: (payload: EventCreatePayload) => createEvent(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['events'] })
      qc.invalidateQueries({ queryKey: ['events', { club_id: clubId }] })
      handleClose()
    },
  })

  function handleSubmit() {
    if (!title.trim() || !startAt) return

    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)

    mutation.mutate({
      club_id: clubId,
      title: title.trim(),
      description: description.trim() || undefined,
      event_type: eventType,
      tags: tags.length > 0 ? tags : undefined,
      venue: venue.trim() || undefined,
      start_at: new Date(startAt).toISOString(),
      end_at: endAt ? new Date(endAt).toISOString() : undefined,
      seat_limit: seatLimit ? parseInt(seatLimit, 10) : undefined,
    })
  }

  const errResp = (mutation.error as { response?: { status?: number; data?: { detail?: string } } })?.response
  const errorMsg = errResp?.data?.detail

  return (
    <Modal open={open} onClose={handleClose} eyebrow={`Posting for ${clubName}`} title="Pin a new event">
      {errorMsg && (
        <div className="mb-4 rounded-lg bg-alert/10 text-alert px-3 py-2 text-sm">
          {errResp?.status === 403
            ? 'Only the club president or a college admin can post events for this club.'
            : errorMsg}
        </div>
      )}

      <div className="space-y-4">
        <Field label="Title">
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Intro to Robotics Workshop"
            autoFocus
          />
        </Field>

        <Field label="Description">
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="What's happening, who should come, anything to bring…"
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Starts">
            <Input
              type="datetime-local"
              value={startAt}
              onChange={(e) => setStartAt(e.target.value)}
            />
          </Field>
          <Field label="Ends" hint="Optional">
            <Input
              type="datetime-local"
              value={endAt}
              onChange={(e) => setEndAt(e.target.value)}
              min={startAt}
            />
          </Field>
        </div>

        <Field label="Venue">
          <Input
            value={venue}
            onChange={(e) => setVenue(e.target.value)}
            placeholder="e.g. Seminar Hall 2, Block C"
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Seat limit" hint="Leave blank for unlimited">
            <Input
              type="number"
              min={1}
              value={seatLimit}
              onChange={(e) => setSeatLimit(e.target.value)}
              placeholder="e.g. 60"
            />
          </Field>
          <Field label="Tags" hint="Comma separated">
            <Input
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="workshop, beginner"
            />
          </Field>
        </div>

        <Field label="Who can RSVP?">
          <Select value={eventType} onChange={(e) => setEventType(e.target.value as EventCreatePayload['event_type'])}>
            {EVENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label} — {t.hint}</option>
            ))}
          </Select>
        </Field>

        <button
          onClick={handleSubmit}
          disabled={mutation.isPending || !title.trim() || !startAt}
          className="w-full bg-rust hover:bg-rust/90 disabled:opacity-50 text-white font-display font-semibold rounded-lg py-2.5 text-sm transition-colors"
        >
          {mutation.isPending ? 'Pinning…' : 'Pin event to the board'}
        </button>
      </div>
    </Modal>
  )
}
