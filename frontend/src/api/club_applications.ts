import axiosInstance from './axiosInstance'

export type ApplicationStatus = 'pending' | 'approved' | 'rejected'

export interface NewClubApplication {
  id: number
  applicant_id: number
  club_name: string
  description?: string
  domain?: string
  faculty_advisor_email?: string
  status: ApplicationStatus
  admin_remarks?: string
  created_at: string
}

export interface NewClubApplicationPayload {
  club_name: string
  description?: string
  domain?: string
  faculty_advisor_email?: string
}

/** Any authenticated user — apply to register a brand new club. */
export async function applyForNewClub(payload: NewClubApplicationPayload): Promise<NewClubApplication> {
  const { data } = await axiosInstance.post('/club-applications', payload)
  return data
}

/** college_admin only — list all club applications, optionally filtered by status. */
export async function getClubApplications(status?: ApplicationStatus): Promise<NewClubApplication[]> {
  const { data } = await axiosInstance.get('/club-applications', { params: status ? { status } : {} })
  return data
}

/** college_admin only — approve or reject a club application. */
export async function reviewClubApplication(
  appId: number,
  decision: 'approved' | 'rejected',
  admin_remarks?: string,
): Promise<NewClubApplication> {
  const { data } = await axiosInstance.patch(`/club-applications/${appId}`, { decision, admin_remarks })
  return data
}
