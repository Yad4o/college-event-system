import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Navbar from '../components/Navbar'
import EmptyState from '../components/EmptyState'
import {
  getNotifications,
  markRead,
  markAllRead,
  type Notification,
} from '../api/notifications'

const API_URL = import.meta.env.VITE_API_URL as string
const WS_URL = API_URL.replace(/^http/, 'ws')

// ── type → tone ─────────────────────────────────────────────────────────────
type Tone = 'rust' | 'pine' | 'gold' | 'slate' | 'alert' | 'neutral'

function notifTone(type: string): Tone {
  const map: Record<string, Tone> = {
    rsvp_confirmed:     'pine',
    rsvp_waitlisted:    'gold',
    event_reminder:     'slate',
    certificate_ready:  'gold',
    club_announcement:  'rust',
    recruitment_update: 'rust',
  }
  return map[type] ?? 'neutral'
}

const TONE_CLASSES: Record<Tone, string> = {
  rust:    'bg-rust/10 text-rust',
  pine:    'bg-pine/10 text-pine',
  gold:    'bg-gold/15 text-[#9c6a1f]',
  slate:   'bg-[#5B7FBE]/10 text-[#5B7FBE]',
  alert:   'bg-alert/10 text-alert',
  neutral: 'bg-ink/5 text-ink/55',
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

// ── single notification row ────────────────────────────────────────────────
function NotifRow({ notif }: { notif: Notification }) {
  const qc = useQueryClient()
  const tone = notifTone(notif.notification_type)

  const readMut = useMutation({
    mutationFn: () => markRead(notif.id),
    onSuccess: (updated) => {
      qc.setQueryData(['notifications'], (old: Notification[] | undefined) =>
        old?.map((n) => (n.id === updated.id ? updated : n))
      )
    },
  })

  const inner = (
    <div
      className={`flex items-start gap-3 px-5 py-4 transition-colors ${
        notif.is_read ? '' : 'bg-rust/[0.03]'
      }`}
    >
      {/* Unread indicator */}
      <div className="mt-2 flex-shrink-0">
        <span
          className={`block w-1.5 h-1.5 rounded-full ${
            notif.is_read ? 'bg-transparent' : 'bg-rust'
          }`}
        />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span
            className={`stamp-label inline-flex items-center px-2 py-0.5 rounded-full ${TONE_CLASSES[tone]}`}
          >
            {notif.notification_type.replace(/_/g, ' ')}
          </span>
          <span className="text-xs text-ink/35 font-mono">{timeAgo(notif.created_at)}</span>
        </div>
        <p className={`text-sm leading-snug ${notif.is_read ? 'text-ink/60' : 'text-ink font-medium'}`}>
          {notif.title}
        </p>
        <p className="text-sm text-ink/45 mt-0.5 leading-snug">{notif.message}</p>
      </div>

      {!notif.is_read && (
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            readMut.mutate()
          }}
          disabled={readMut.isPending}
          className="flex-shrink-0 stamp-label text-ink/35 hover:text-rust disabled:opacity-50 transition-colors mt-1"
        >
          Mark read
        </button>
      )}
    </div>
  )

  if (notif.link_url) {
    return (
      <Link
        to={notif.link_url}
        className="block border-b border-dashed border-ink/5 last:border-0 hover:bg-ink/[0.015] transition-colors"
      >
        {inner}
      </Link>
    )
  }

  return (
    <div className="border-b border-dashed border-ink/5 last:border-0">{inner}</div>
  )
}

// ── main page ──────────────────────────────────────────────────────────────
export default function Notifications() {
  const qc = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)

  const { data: notifications, isLoading, isError } = useQuery({
    queryKey: ['notifications'],
    queryFn: getNotifications,
    refetchInterval: 60_000,
  })

  // WebSocket real-time push
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    const ws = new WebSocket(`${WS_URL}/ws/notifications?token=${token}`)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data) as {
          type: string
          id: number
          notification_type: string
          title: string
          message: string
          link_url?: string
          is_read: boolean
        }
        if (msg.type !== 'notification') return

        const newNotif: Notification = {
          id: msg.id,
          notification_type: msg.notification_type,
          title: msg.title,
          message: msg.message,
          is_read: msg.is_read,
          link_url: msg.link_url,
          created_at: new Date().toISOString(),
        }

        qc.setQueryData(['notifications'], (old: Notification[] | undefined) =>
          old ? [newNotif, ...old] : [newNotif]
        )
      } catch {
        // ignore malformed push
      }
    }

    ws.onerror = () => ws.close()

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [qc])

  const markAllMut = useMutation({
    mutationFn: markAllRead,
    onSuccess: () => {
      qc.setQueryData(['notifications'], (old: Notification[] | undefined) =>
        old?.map((n) => ({ ...n, is_read: true }))
      )
    },
  })

  const unreadCount = notifications?.filter((n) => !n.is_read).length ?? 0

  return (
    <div className="min-h-screen bg-paper">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <p className="stamp-label text-rust mb-1">What's happening</p>
            <h1 className="text-2xl font-display font-bold text-ink">
              Notifications
              {unreadCount > 0 && (
                <span className="ml-2 text-base font-medium text-rust">· {unreadCount} new</span>
              )}
            </h1>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={() => markAllMut.mutate()}
              disabled={markAllMut.isPending}
              className="flex-shrink-0 stamp-label text-ink/40 hover:text-rust disabled:opacity-50 transition-colors mt-1"
            >
              {markAllMut.isPending ? 'Marking…' : 'Mark all read'}
            </button>
          )}
        </div>

        <div className="pin-card rounded-2xl border border-ink/5 shadow-pin overflow-hidden">
          {isLoading && (
            <div className="divide-y divide-dashed divide-ink/5">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="px-5 py-4 animate-pulse flex gap-3">
                  <div className="w-1.5 h-1.5 mt-2 rounded-full bg-ink/5 flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 bg-ink/5 rounded w-1/4" />
                    <div className="h-4 bg-ink/5 rounded w-3/4" />
                    <div className="h-3 bg-ink/5 rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {isError && (
            <EmptyState
              tone="error"
              title="Couldn't load notifications"
              message="Something went wrong. Try refreshing the page."
              icon={
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                </svg>
              }
            />
          )}

          {!isLoading && !isError && notifications?.length === 0 && (
            <EmptyState
              title="All quiet"
              message="Activity from events, clubs, and certificates will appear here."
              icon={
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                  <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                </svg>
              }
            />
          )}

          {!isLoading && !isError && notifications?.map((n) => (
            <NotifRow key={n.id} notif={n} />
          ))}
        </div>
      </div>
    </div>
  )
}
