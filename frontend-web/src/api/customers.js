import api from './client'

// Register a new customer (no JWT needed)
export const registerCustomer = (data) =>
  api.post('/gateway/customers/api/customers/register/', data).then((r) => r.data)

// Get customer profile
export const getCustomer = (customerId) =>
  api.get(`/gateway/customers/api/customers/${customerId}/`).then((r) => r.data)

// Update customer profile
export const updateCustomer = (customerId, data) =>
  api.put(`/gateway/customers/api/customers/${customerId}/`, data).then((r) => r.data)

// List all active customers (manager use)
export const getCustomerList = () =>
  api.get('/gateway/customers/api/customers/').then((r) => (Array.isArray(r.data) ? r.data : []))
