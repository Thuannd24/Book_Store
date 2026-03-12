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

// Get ALL orders (for staff/manager)
export const getAllOrders = () =>
  api.get('/gateway/orders/api/orders/').then((r) => (Array.isArray(r.data) ? r.data : []))

// Update order status (staff action)
export const updateOrderStatus = (orderId, newStatus) =>
  api.patch(`/gateway/orders/api/orders/${orderId}/status/`, { status: newStatus }).then((r) => r.data)

// Get promos for a customer
export const getCustomerPromos = (customerId) =>
  api
    .get(`/gateway/orders/api/customers/${customerId}/promos/`)
    .then((r) => (r.data && Array.isArray(r.data.promos) ? r.data.promos : []))
