import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginStaff } from '../../api/staff'
import { useAuth } from '../../contexts/AuthContext'
import { Input } from '../../components/common/Input'
import { BaseLoginForm } from '../../components/common/BaseLoginForm'

export default function StaffLoginPage() {
  const { loginAsStaff } = useAuth()
  const navigate = useNavigate()
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
      const user = await loginStaff(form)
      loginAsStaff(user)
      navigate('/staff/books')
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
      icon="🧑‍💼"
      title="Staff Login"
      subtitle="Access the staff management panel"
      loading={loading}
      apiError={apiError}
      onSubmit={handleSubmit}
      formFields={
        <>
          <Input label="Email" type="email" required placeholder="staff@example.com" {...field('email')} />
          <Input label="Password" type="password" required placeholder="••••••••" {...field('password')} />
        </>
      }
    />
  )
}
