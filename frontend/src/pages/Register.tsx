
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import AuthLayout from '../components/AuthLayout'
import { Field, Input, Select } from '../components/FormField'

export default function Register() {
  const { register } = useAuth()

  const [form, setForm] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'student' as 'student' | 'college_admin',
    admin_code: '',
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
      setError('Name, email, and password are required.')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setError('')
    setLoading(true)
    try {
      await register({
        email: form.email,
        full_name: form.full_name,
        password: form.password,
        role: form.role,
        admin_code: form.role === 'college_admin' ? form.admin_code || undefined : undefined,
        branch: form.branch || undefined,
        year: form.year ? parseInt(form.year, 10) : undefined,
      })
    } catch (err: unknown) {
      const resp = (err as { response?: { status: number; data?: { detail?: string } } })?.response
      if (resp?.status === 400) {
        setError(resp.data?.detail ?? 'That email is already registered.')
      } else if (resp?.status === 403) {
        setError(resp.data?.detail ?? 'Invalid admin registration code.')
      } else if (resp?.status === 422) {
        setError("Check your details — something doesn't look right.")
      } else {
        setError('Something went wrong. Try again in a moment.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <p className="stamp-label text-rust mb-1">Join the board</p>
      <h1 className="text-2xl font-display font-bold text-ink mb-1">Create your account</h1>
      <p className="text-sm text-ink/45 mb-6">
        Your account is ready instantly — no email step.
      </p>

      {error && (
        <div className="mb-4 rounded-lg bg-alert/10 border border-alert/20 text-alert px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-4">
        <Field label="Full name">
          <Input
            value={form.full_name}
            onChange={(e) => set('full_name', e.target.value)}
            placeholder="Jane Doe"
          />
        </Field>

        <Field label="Email">
          <Input
            type="email"
            value={form.email}
            onChange={(e) => set('email', e.target.value)}
            placeholder="you@college.edu"
          />
        </Field>

        <Field label="Password" hint="At least 8 characters">
          <Input
            type="password"
            value={form.password}
            onChange={(e) => set('password', e.target.value)}
            placeholder="••••••••"
          />
        </Field>

        <Field label="Account type">
          <Select value={form.role} onChange={(e) => set('role', e.target.value)}>
            <option value="student">Student</option>
            <option value="college_admin">College admin</option>
          </Select>
        </Field>

        {form.role === 'college_admin' && (
          <Field label="Admin code" hint="Provided by your institution — required to register as admin">
            <Input
              type="password"
              value={form.admin_code}
              onChange={(e) => set('admin_code', e.target.value)}
              placeholder="Enter registration code"
            />
          </Field>
        )}

        <div className="grid grid-cols-2 gap-3">
          <Field label="Branch" hint="Optional">
            <Input
              value={form.branch}
              onChange={(e) => set('branch', e.target.value)}
              placeholder="Computer Engg"
            />
          </Field>
          <Field label="Year" hint="Optional">
            <Input
              type="number"
              min={1}
              max={6}
              value={form.year}
              onChange={(e) => set('year', e.target.value)}
              placeholder="2"
            />
          </Field>
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-rust hover:bg-rust/90 disabled:opacity-50 text-white font-display font-semibold rounded-lg py-2.5 text-sm transition-colors"
        >
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </div>

      <p className="mt-6 text-center text-sm text-ink/45">
        Already on the board?{' '}
        <Link to="/login" className="text-rust hover:underline font-medium">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
