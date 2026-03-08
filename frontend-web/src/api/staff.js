import api from './client'

// Staff register
export const registerStaff = (data) =>
  api.post('/gateway/staff/api/staff/register/', data).then((r) => r.data)

// Get staff profile
export const getStaff = (staffId) =>
  api.get(`/gateway/staff/api/staff/${staffId}/`).then((r) => r.data)
