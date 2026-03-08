import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { authLogin } from '../../api/auth'
import { useAuth } from '../../contexts/AuthContext'
import { Input } from '../../components/common/Input'
import { BaseLoginForm } from '../../components/common/BaseLoginForm'

export default function LoginPage() {
  const { loginWithTokens } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/'
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [apiError, setApiError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.email.includes('@')) errs.email = 'Enter a valid email'
    if (!form.password) errs.password = 'Password is required'
    if (Object.keys(errs).length) { setErrors(errs); return }
    setLoading(true)
    setApiError('')
    try {
      const data = await authLogin(form.email, form.password, 'CUSTOMER')
      loginWithTokens(data)
      navigate(from, { replace: true })
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const field = (name) => ({
    value: form[name],
    onChange: (e) => { setForm((f) => ({ ...f, [name]: e.target.value })); setErrors((er) => ({ ...er, [name]: '' })) },
    error: errors[name],
  })

  return (
    <BaseLoginForm
      icon="📚"
      title="Welcome Back"
      subtitle="Login to your account"
      loading={loading}
      apiError={apiError}
      onSubmit={handleSubmit}
      containerClassName="min-h-[80vh] flex items-center justify-center"
      formFields={
        <>
          <Input label="Email" type="email" required placeholder="you@example.com" {...field('email')} />
          <Input label="Password" type="password" required placeholder="••••••••" {...field('password')} />
        </>
      }
      footer={
        <>
          <p className="text-center text-sm text-gray-500 mt-5">
            Don't have an account?{' '}
            <Link to="/register" className="text-indigo-600 hover:underline font-medium">
              Register
            </Link>
          </p>
          <div className="mt-4 pt-4 border-t text-center">
            <p className="text-xs text-gray-400">Staff or Manager?</p>
            <div className="flex justify-center gap-4 mt-1">
              <Link to="/staff/login" className="text-xs text-indigo-500 hover:underline">Staff Login</Link>
              <Link to="/manager/login" className="text-xs text-indigo-500 hover:underline">Manager Login</Link>
            </div>
          </div>
        </>
      }
    />
  )
}
