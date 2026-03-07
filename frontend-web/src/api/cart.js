import api from './client'

// Get cart for a customer
export const getCart = (customerId) =>
  api.get(`/gateway/carts/api/carts/customer/${customerId}/`).then((r) => r.data)

// Add item to cart
export const addToCart = (customerId, data) =>
  api.post(`/gateway/carts/api/carts/customer/${customerId}/items/`, data).then((r) => r.data)

// Update item quantity
export const updateCartItem = (itemId, data) =>
  api.put(`/gateway/carts/api/carts/items/${itemId}/`, data).then((r) => r.data)

// Remove item
export const removeCartItem = (itemId) =>
  api.delete(`/gateway/carts/api/carts/items/${itemId}/`).then((r) => r.data)

// Clear cart
export const clearCart = (customerId) =>
  api.delete(`/gateway/carts/api/carts/customer/${customerId}/clear/`).then((r) => r.data)
