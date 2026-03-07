import api from './client'

// Place an order
export const createOrder = (data) =>
  api.post('/gateway/orders/api/orders/', data).then((r) => r.data)

// Get orders for a customer
export const getCustomerOrders = (customerId) =>
  api.get(`/gateway/orders/api/orders/customer/${customerId}/`).then((r) => (Array.isArray(r.data) ? r.data : []))

// Get single order
export const getOrder = (orderId) =>
  api.get(`/gateway/orders/api/orders/${orderId}/`).then((r) => r.data)
