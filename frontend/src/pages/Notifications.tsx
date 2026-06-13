import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Navbar from '../components/Navbar'
import {
  getNotifications,
  markRead,
  markAllRead,
  type Notification,
} from '../api/notifications'

const API_URL = import.meta.env.VITE_API_URL as string
const WS_URL = API_URL.replace(/^http/, 'ws')

// ── type badge colours ─────────────────────────────────────────────────────
function typeBadge(type: string) {
  const map: Record<string, string> = {
    rsvp_confirmed:    'bg-green-50 text-green-600',
    rsvp_waitlisted:   'bg-amber-50 text-amber-600',
    event_reminder:    'bg-blue-50 text-blue-600',
    certificate_ready: 'bg-purple-50 text-purple-600',
    club_announcement: 'bg-indigo-50 text-indigo-600',
    recruitment_update:'bg-orange-50 text-orange-600',
    general:           'bg-gray-100 text-gray-500',
  }
  return map[type] ?? 'bg-gray-100 text-gray-500'
}

function typeLabel(type: string) {
  return type.replace(/_/g, ' ')
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
        notif.is_read ? 'bg-white' : 'bg-blue-50/40'
      }`}
    >
      {/* Unread dot */}
      <div className="mt-1.5 flex-shrink-0">
        {!notif.is_read ? (
          <span className="block w-2 h-2 rounded-full bg-blue-500" />
        ) : (
          <span className="block w-2 h-2 rounded-full bg-transparent" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${typeBadge(
              notif.notification_type
            )}`}
          >
            {typeLabel(notif.notification_type)}
          </span>
          <span className="text-xs text-gray-400">{timeAgo(notif.created_at)}</span>
        </div>
        <p className="text-sm font-semibold text-gray-800">{notif.title}</p>
        <p className="text-sm text-gray-500 leading-snug mt-0.5">{notif.message}</p>
      </div>

      {!notif.is_read && (
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            readMut.mutate()
          }}
          disabled={readMut.isPending}
          className="flex-shrink-0 text-xs text-gray-400 hover:text-blue-600 disabled:opacity-50 transition-colors mt-1"
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
        className="block border-b border-gray-50 last:border-0 hover:bg-gray-50/60 transition-colors"
      >
        {inner}
      </Link>
    )
  }

  return (
    <div className="border-b border-gray-50 last:border-0">{inner}</div>
  )
}

// ── main page ──────────────────────────────────────────────────────────────
export default function Notifications() {
  const qc = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)

  const { data: notifications, isLoading, isError } = useQuery({
    queryKey: ['notifications'],
    queryFn: getNotifications,
    refetchInterval: 60_000, // background poll every 60s as fallback
  })

  // ── WebSocket real-time push ──────────────────────────────────────────────
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

        // Prepend to list (unread → top)
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
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              Notifications
              {unreadCount > 0 && (
                <span className="ml-2 text-base font-semibold text-blue-600">
                  ({unreadCount} new)
                </span>
              )}
            </h1>
          </div>
          {unreadCount > 0 && (
            <button
              onClick={() => markAllMut.mutate()}
              disabled={markAllMut.isPending}
              className="text-sm text-blue-500 hover:text-blue-700 disabled:opacity-50 font-medium transition-colors"
            >
              {markAllMut.isPending ? 'Marking…' : 'Mark all as read'}
            </button>
          )}
        </div>

        {/* Content */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          {isLoading && (
            <div className="divide-y divide-gray-50">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="px-5 py-4 animate-pulse flex gap-3">
                  <div className="w-2 h-2 mt-1.5 rounded-full bg-gray-100 flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 bg-gray-100 rounded w-1/4" />
                    <div className="h-4 bg-gray-100 rounded w-3/4" />
                    <div className="h-3 bg-gray-100 rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {isError && (
            <p className="text-center py-12 text-red-500 text-sm">
              Failed to load notifications.
            </p>
          )}

          {!isLoading && !isError && notifications?.length === 0 && (
            <div className="text-center py-16">
              <p className="text-gray-400 text-sm">No notifications yet.</p>
              <p className="text-gray-300 text-xs mt-1">
                Activity from events, clubs, and certificates will appear here.
              </p>
            </div>
          )}

          {!isLoading &&
            !isError &&
            notifications?.map((n) => <NotifRow key={n.id} notif={n} />)}
        </div>
      </div>
    </div>
  )
}
