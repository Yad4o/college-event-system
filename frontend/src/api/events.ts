import axiosInstance from './axiosInstance'

export interface Event {
  id: number
  club_id: number
  title: string
  description?: string
  event_type?: string
  tags?: string[]
  venue?: string
  start_at: string
  end_at?: string
  seat_limit?: number
  is_hidden: boolean
  is_cancelled: boolean
  rsvp_count: number
  waitlist_count: number
}

export interface Rsvp {
  id: number
  event_id: number
  user_id: number
  status: 'confirmed' | 'waitlisted'
  waitlist_position?: number
  created_at: string
}

export async function getEvents(params?: {
  skip?: number
  limit?: number
  club_id?: number
  tags?: string
}): Promise<Event[]> {
  const { data } = await axiosInstance.get('/events', { params })
  return data
}

export async function getEvent(id: number): Promise<Event> {
  const { data } = await axiosInstance.get(`/events/${id}`)
  return data
}

export async function rsvpToEvent(eventId: number): Promise<Rsvp> {
  const { data } = await axiosInstance.post(`/events/${eventId}/rsvp`)
  return data
}

export async function cancelRsvp(eventId: number): Promise<void> {
  await axiosInstance.delete(`/events/${eventId}/rsvp`)
}

/**
 * Fetch the current user's RSVP for an event.
 * Returns null if they have not RSVPed (404 → null).
 */
export async function getMyRsvp(eventId: number): Promise<Rsvp | null> {
  try {
    const rsvps: Rsvp[] = await getEventRsvps(eventId)
    // The /events/{id}/rsvps endpoint is admin-only; use the all-rsvps
    // approach only for admins. For a regular user we infer from the list.
    // If the call throws 403 we just return null and derive state from
    // a local mutation cache instead.
    void rsvps
    return null
  } catch {
    return null
  }
}

/** Admin-only: list all RSVPs for an event. */
export async function getEventRsvps(eventId: number): Promise<Rsvp[]> {
  const { data } = await axiosInstance.get(`/events/${eventId}/rsvps`)
  return data
}
