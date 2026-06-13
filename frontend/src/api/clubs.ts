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
}

export interface Membership {
  user_id: number
  club_id: number
  role: string
  joined_at: string
}

export async function getClubs(params?: { skip?: number; limit?: number; domain?: string }): Promise<Club[]> {
  const { data } = await axiosInstance.get('/clubs', { params })
  return data
}

export async function getClub(id: number): Promise<Club> {
  const { data } = await axiosInstance.get(`/clubs/${id}`)
  return data
}

export async function joinClub(id: number): Promise<void> {
  await axiosInstance.post(`/clubs/${id}/join`)
}
