import { useEffect, useState } from 'react'
import { getCustomer, updateCustomer } from '../../api/customers'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../../components/common/Button'
import { Input } from '../../components/common/Input'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { Spinner } from '../../components/common/Spinner'

export default function ProfilePage() {
  const { customer } = useAuth()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [form, setForm] = useState({ full_name: '', phone: '', address: '' })

  useEffect(() => {
    getCustomer(customer.id)
      .then((data) => {
        setProfile(data)
        setForm({
          full_name: data.full_name || '',
          phone: data.phone || '',
          address: data.address || '',
        })
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [customer.id])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')
    try {
      const updated = await updateCustomer(customer.id, form)
      setProfile(updated)
      setSuccess('✅ Profile updated successfully!')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="max-w-lg mx-auto flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-gray-800">My Profile</h1>

      <div className="bg-white rounded-2xl border p-6 flex flex-col gap-5">
        {/* Account info (read-only) */}
        <div className="flex flex-col gap-1">
          <p className="text-xs text-gray-400">Email</p>
          <p className="font-medium text-gray-800">{profile?.email}</p>
        </div>

        <div className="border-t pt-4">
          <h2 className="font-semibold text-gray-700 mb-4">Edit Profile</h2>
          <ErrorBanner message={error} />
          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm mb-4">
              {success}
            </div>
          )}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              label="Full Name"
              placeholder="Your full name"
              value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            />
            <Input
              label="Phone"
              placeholder="Your phone number"
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            />
            <Input
              label="Address"
              placeholder="Your shipping address"
              value={form.address}
              onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
            />
            <Button type="submit" loading={saving}>Save Changes</Button>
          </form>
        </div>
      </div>
    </div>
  )
}
