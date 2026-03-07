import api from './client'

// Get recommendations for a customer
export const getRecommendations = (customerId, limit = 8) =>
  api
    .get(`/gateway/recommendations/api/recommendations/customer/${customerId}/`, { params: { limit } })
    .then((r) => r.data)
