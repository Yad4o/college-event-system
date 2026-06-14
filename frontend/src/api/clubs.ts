import axiosInstance from './axiosInstance'

export interface Club {
  id: number
  name: string
  description?: string
  domain?: string
  logo_url?: string
  join_type: 'open' | 'invite_only'
  is_active: boolean
  is_suspended: boolean
  member_count: number
  my_role?: string
}

export interface Membership {
  user_id: number
  club_id: number
  role: string
  joined_at: string
}

export interface ClubCreatePayload {
  name: string
  description?: string
  domain?: string
  join_type?: 'open' | 'invite_only'
}

export interface JoinRequest {
  id: number
  applicant_id: number
  club_name: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}

export async function getClubs(params?: { skip?: number; limit?: number; domain?: string }): Promise<Club[]> {
  const { data } = await axiosInstance.get('/clubs', { params })
  return data
}

export async function getClub(id: number): Promise<Club> {
  const { data } = await axiosInstance.get(`/clubs/${id}`)
  return data
}

export async function createClub(payload: ClubCreatePayload): Promise<Club> {
  const { data } = await axiosInstance.post('/clubs', payload)
  return data
}

export async function joinClub(id: number): Promise<void> {
  await axiosInstance.post(`/clubs/${id}/join`)
}

/** Club admin only — list pending join requests for invite-only clubs. */
export async function getJoinRequests(clubId: number): Promise<JoinRequest[]> {
  const { data } = await axiosInstance.get(`/clubs/${clubId}/join-requests`)
  return data
}

/** Club admin only — approve or reject a pending join request. */
export async function decideJoinRequest(
  clubId: number,
  requestId: number,
  decision: 'approved' | 'rejected',
): Promise<JoinRequest> {
  const { data } = await axiosInstance.patch(
    `/clubs/${clubId}/join-requests/${requestId}`,
    {},
    { params: { decision } },
  )
  return data
}

/** Club admin only — remove a member from the club. */
export async function removeMember(clubId: number, userId: number): Promise<void> {
  await axiosInstance.delete(`/clubs/${clubId}/members/${userId}`)
}
