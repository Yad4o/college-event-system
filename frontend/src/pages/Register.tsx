import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Register() {
  const { register } = useAuth()

  const [form, setForm] = useState({
    email: '',
    full_name: '',
    password: '',
    branch: '',
    year: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function set(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit() {
    if (!form.email || !form.full_name || !form.password) {
      setError('Email, full name, and password are required.')
      return
    }
    setError('')
    setLoading(true)
    try {
      await register({
        email: form.email,
        full_name: form.full_name,
        password: form.password,
        branch: form.branch || undefined,
        year: form.year ? parseInt(form.year, 10) : undefined,
      })
    } catch (err: unknown) {
      const status = (err as { response?: { status: number; data?: { detail?: string } } })?.response
      if (status?.status === 400) {
        setError(status.data?.detail ?? 'Email already registered.')
      } else if (status?.status === 422) {
        setError('Please check your input — some fields are invalid.')
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-10">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-md p-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">Create account</h1>
        <p className="text-sm text-gray-500 mb-6">College Event System</p>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-600 px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {(
            [
              { label: 'Full name', field: 'full_name', type: 'text', placeholder: 'Jane Doe' },
              { label: 'Email', field: 'email', type: 'email', placeholder: 'you@college.edu' },
              { label: 'Password', field: 'password', type: 'password', placeholder: '••••••••' },
              { label: 'Branch (optional)', field: 'branch', type: 'text', placeholder: 'Computer Engineering' },
              { label: 'Year (optional)', field: 'year', type: 'number', placeholder: '2' },
            ] as const
          ).map(({ label, field, type, placeholder }) => (
            <div key={field}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input
                type={type}
                value={form[field]}
                onChange={(e) => set(field, e.target.value)}
                placeholder={placeholder}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold rounded-lg py-2 text-sm transition-colors"
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-gray-500">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-600 hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
