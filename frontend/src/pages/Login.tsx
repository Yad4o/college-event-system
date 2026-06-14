
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import AuthLayout from '../components/AuthLayout'
import { Field, Input } from '../components/FormField'

export default function Login() {
  const { login } = useAuth()
  const location = useLocation()
  const successMsg = (location.state as { message?: string })?.message

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit() {
    if (!email || !password) {
      setError('Enter your email and password to continue.')
      return
    }
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch (err: unknown) {
      const status = (err as { response?: { status: number } })?.response?.status
      if (status === 401) {
        setError('That email and password don't match.')
      } else if (status === 403) {
        setError('This account is disabled. Contact your college admin.')
      } else {
        setError('Something went wrong. Try again in a moment.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <p className="stamp-label text-rust mb-1">Welcome back</p>
      <h1 className="text-2xl font-display font-bold text-ink mb-1">Sign in</h1>
      <p className="text-sm text-ink/45 mb-6">Pick up where you left off on the board.</p>

      {successMsg && (
        <div className="mb-4 rounded-lg bg-pine/10 border border-pine/20 text-pine px-4 py-3 text-sm">
          {successMsg}
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-alert/10 border border-alert/20 text-alert px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <Field label="Email">
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            placeholder="you@college.edu"
          />
        </Field>

        <Field label="Password">
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            placeholder="••••••••"
          />
        </Field>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-rust hover:bg-rust/90 disabled:opacity-50 text-white font-display font-semibold rounded-lg py-2.5 text-sm transition-colors"
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
      </div>

      <p className="mt-6 text-center text-sm text-ink/45">
        New here?{' '}
        <Link to="/register" className="text-rust hover:underline font-medium">
          Create an account
        </Link>
      </p>
    </AuthLayout>
  )
}
