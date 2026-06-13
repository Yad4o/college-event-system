import axiosInstance from './axiosInstance'

export interface Notification {
  id: number
  notification_type: string
  title: string
  message: string
  is_read: boolean
  link_url?: string
  created_at: string
}

export async function getNotifications(): Promise<Notification[]> {
  const { data } = await axiosInstance.get('/notifications')
  return data
}

export async function markRead(id: number): Promise<Notification> {
  const { data } = await axiosInstance.patch(`/notifications/${id}/read`)
  return data
}

export async function markAllRead(): Promise<void> {
  await axiosInstance.patch('/notifications/read-all')
}
