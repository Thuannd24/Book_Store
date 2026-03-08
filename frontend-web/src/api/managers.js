import api from './client'

// Manager register
export const registerManager = (data) =>
  api.post('/gateway/managers/api/managers/register/', data).then((r) => r.data)

// Get manager dashboard summary
export const getDashboardSummary = () =>
  api.get('/gateway/managers/api/manager/dashboard/summary/').then((r) => r.data)
