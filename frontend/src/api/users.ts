import axiosInstance from './axiosInstance'

export interface UserMe {
  id: number
  email: string
  full_name: string
  role: string
  is_email_verified: boolean
  branch?: string
  year?: number
  bio?: string
  skills?: string
  profile_picture?: string
}

export interface UserUpdate {
  full_name?: string
  bio?: string
  skills?: string
  branch?: string
  year?: number
}

export async function getMe(): Promise<UserMe> {
  const { data } = await axiosInstance.get('/users/me')
  return data
}

export async function updateMe(payload: UserUpdate): Promise<UserMe> {
  const { data } = await axiosInstance.patch('/users/me', payload)
  return data
}
