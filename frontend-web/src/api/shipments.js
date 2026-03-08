import api from './client'

// Get shipment by ID
export const getShipment = (shipmentId) =>
  api.get(`/gateway/shipments/api/shipments/${shipmentId}/`).then((r) => r.data)

// Get shipments by order
export const getShipmentsByOrder = (orderId) =>
  api.get(`/gateway/shipments/api/shipments/order/${orderId}/`).then((r) => (Array.isArray(r.data) ? r.data : []))
