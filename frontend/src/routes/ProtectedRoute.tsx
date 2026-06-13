import { Navigate, Outlet } from 'react-router-dom'

/**
 * Wraps protected pages.
 * Redirects to /login if no access_token is found in localStorage.
 */
export default function ProtectedRoute() {
  const token = localStorage.getItem('access_token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
