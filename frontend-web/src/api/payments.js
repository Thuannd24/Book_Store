import api from './client'

// Get payment by ID
export const getPayment = (paymentId) =>
  api.get(`/gateway/payments/api/payments/${paymentId}/`).then((r) => r.data)

// Get payments by order
export const getPaymentsByOrder = (orderId) =>
  api.get(`/gateway/payments/api/payments/order/${orderId}/`).then((r) => (Array.isArray(r.data) ? r.data : []))
