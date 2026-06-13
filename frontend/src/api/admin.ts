import axiosInstance from './axiosInstance'

export interface DashboardStats {
  total_users: number
  total_clubs: number
  active_clubs: number
  suspended_clubs: number
  total_events: number
  upcoming_events: number
  total_rsvps: number
  total_attendance: number
  total_certificates_issued: number
}

export interface AdminUser {
  id: number
  email: string
  full_name: string
  role: string
  is_email_verified: boolean
  branch?: string
  year?: number
}

export interface AdminClub {
  id: number
  name: string
  description?: string
  domain?: string
  logo_url?: string
  join_type: string
  is_active: boolean
  is_suspended: boolean
  member_count: number
}

export interface BudgetReportItem {
  club_id: number
  club_name: string
  total_allocated: number
  total_spent: number
}

export async function getStats(): Promise<DashboardStats> {
  const { data } = await axiosInstance.get('/admin/stats')
  return data
}

export async function getAdminUsers(params?: {
  role?: string
  skip?: number
  limit?: number
}): Promise<AdminUser[]> {
  const { data } = await axiosInstance.get('/admin/users', { params })
  return data
}

export async function changeUserRole(userId: number, role: string): Promise<AdminUser> {
  const { data } = await axiosInstance.patch(`/admin/users/${userId}/role`, { role })
  return data
}

export async function getAdminClubs(): Promise<AdminClub[]> {
  const { data } = await axiosInstance.get('/admin/clubs')
  return data
}

export async function toggleClubSuspension(clubId: number): Promise<AdminClub> {
  const { data } = await axiosInstance.patch(`/admin/clubs/${clubId}/suspend`)
  return data
}

export async function getBudgetReport(): Promise<BudgetReportItem[]> {
  const { data } = await axiosInstance.get('/admin/budget-report')
  return data
}
