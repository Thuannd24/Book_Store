import api from './client'

// Post a review
export const createReview = (data) =>
  api.post('/gateway/reviews/api/reviews/', data).then((r) => r.data)

// Get reviews for a book
export const getBookReviews = (bookId) =>
  api.get(`/gateway/reviews/api/reviews/book/${bookId}/`).then((r) => r.data)

// Get average rating for a book
export const getBookRating = (bookId) =>
  api.get(`/gateway/reviews/api/reviews/book/${bookId}/average/`).then((r) => r.data)

// Get reviews by a customer
export const getCustomerReviews = (customerId) =>
  api.get(`/gateway/reviews/api/reviews/customer/${customerId}/`).then((r) => r.data)

// Get average ratings for all books (for manager/staff display)
export const getBooksSummaryAverages = () =>
  api.get('/gateway/reviews/api/reviews/books/summary/averages/').then((r) => (Array.isArray(r.data) ? r.data : []))
