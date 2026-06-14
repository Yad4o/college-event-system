import { useNavigate } from 'react-router-dom'
import axiosInstance from '../api/axiosInstance'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL as string

interface RegisterData {
  email: string
  full_name: string
  password: string
  role?: 'student' | 'college_admin'
  admin_code?: string
  branch?: string
  year?: number
}

export function useAuth() {
  const navigate = useNavigate()

  async function login(email: string, password: string): Promise<void> {
    const { data } = await axiosInstance.post('/auth/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    navigate('/')
  }

  async function register(data: RegisterData): Promise<void> {
    await axiosInstance.post('/auth/register', data)
    navigate('/login', { state: { message: 'Account created. You can sign in now.' } })
  }

  async function logout(): Promise<void> {
    try {
      await axios.post(`${API_URL}/auth/logout`, {}, { withCredentials: true })
    } catch {
      // Ignore logout errors — clear client state regardless
    }
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  return { login, register, logout }
}
