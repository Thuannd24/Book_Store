import api from './client'

// Get categories
export const getCategories = () =>
  api.get('/gateway/catalog/api/catalog/categories/').then((r) => r.data)

// Get single category
export const getCategory = (id) =>
  api.get(`/gateway/catalog/api/catalog/categories/${id}/`).then((r) => r.data)

// Create category (staff)
export const createCategory = (data) =>
  api.post('/gateway/catalog/api/catalog/categories/', data).then((r) => r.data)

// Update category (staff)
export const updateCategory = (id, data) =>
  api.put(`/gateway/catalog/api/catalog/categories/${id}/`, data).then((r) => r.data)

// Delete category (staff)
export const deleteCategory = (id) =>
  api.delete(`/gateway/catalog/api/catalog/categories/${id}/`)
