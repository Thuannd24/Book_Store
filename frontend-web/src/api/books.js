import api from './client'

// List books with optional filters
export const getBooks = (params = {}) =>
  api.get('/gateway/books/api/books/', { params }).then((r) => r.data)

// Get single book
export const getBook = (bookId) =>
  api.get(`/gateway/books/api/books/${bookId}/`).then((r) => r.data)

// Create book (staff)
export const createBook = (data) =>
  api.post('/gateway/books/api/books/', data).then((r) => r.data)

// Update book (staff)
export const updateBook = (bookId, data) =>
  api.put(`/gateway/books/api/books/${bookId}/`, data).then((r) => r.data)

// Delete book (staff)
export const deleteBook = (bookId) =>
  api.delete(`/gateway/books/api/books/${bookId}/`)
