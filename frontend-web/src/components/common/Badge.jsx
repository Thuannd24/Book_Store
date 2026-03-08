export function Badge({ children, color = 'gray' }) {
  const colors = {
    gray: 'bg-gray-100 text-gray-700',
    green: 'bg-green-100 text-green-700',
    blue: 'bg-blue-100 text-blue-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    red: 'bg-red-100 text-red-700',
    purple: 'bg-purple-100 text-purple-700',
    indigo: 'bg-indigo-100 text-indigo-700',
  }
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${colors[color]}`}>
      {children}
    </span>
  )
}

export const ORDER_STATUS_COLOR = {
  CREATED: 'blue',
  PENDING: 'gray',
  PAYMENT_CREATED: 'yellow',
  PAYMENT_RESERVED: 'yellow',
  SHIPMENT_CREATED: 'purple',
  SHIPMENT_RESERVED: 'purple',
  CONFIRMED: 'green',
  SHIPPING: 'indigo',
  DELIVERED: 'green',
  FAILED: 'red',
  COMPENSATING: 'red',
  COMPENSATED: 'red',
}

export const PAYMENT_STATUS_COLOR = {
  PENDING: 'yellow',
  SUCCESS: 'green',
  FAILED: 'red',
}

export const SHIPMENT_STATUS_COLOR = {
  PENDING: 'yellow',
  RESERVED: 'blue',
  SHIPPING: 'indigo',
  DELIVERED: 'green',
  FAILED: 'red',
}
