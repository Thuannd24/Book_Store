# API Reference
High-level map of the 12 Django REST services. Every service mounts its public API under `/api/` on its container port; `api-gateway` proxies client traffic under `/api/gateway/<service_key>/...`.

## Services at a Glance
| Service | Host Port | Purpose | Public Base |
| --- | --- | --- | --- |
| api-gateway | 8080 | Single entry point/proxy | `/api/gateway/*` |
| staff-service | 8081 | Staff accounts | `/api/` |
| manager-service | 8082 | Managers + dashboard | `/api/` |
| customer-service | 8083 | Customers + profiles | `/api/` |
| catalog-service | 8084 | Categories | `/api/` |
| book-service | 8085 | Books & inventory snapshot | `/api/` |
| cart-service | 8086 | Carts & items | `/api/` |
| order-service | 8087 | Orders lifecycle | `/api/` |
| ship-service | 8088 | Shipments | `/api/` |
| pay-service | 8089 | Payments | `/api/` |
| comment-rate-service | 8090 | Reviews & averages | `/api/` |
| recommender-ai-service | 8091 | Rule-based recommendations | `/api/` |

## Major Public Endpoints (per service)
- api-gateway: `GET /api/health/`; proxy everything under `/api/gateway/<service>/<path>` to downstream services.
- staff-service: `POST /api/staff/register/`, `POST /api/staff/login/`, `GET /api/staff/{staff_id}/`, `GET /api/staff/`, `GET /api/health/`.
- manager-service: `POST /api/managers/register/`, `POST /api/managers/login/`, `GET /api/managers/{manager_id}/`, `GET /api/manager/dashboard/summary/`, `GET /api/health/`.
- customer-service: `POST /api/customers/register/`, `POST /api/customers/login/`, `GET/PUT /api/customers/{customer_id}/`, `GET /api/customers/` (list), `GET /api/health/`.
- catalog-service: `GET/POST /api/catalog/categories/`, `GET/PUT/DELETE /api/catalog/categories/{category_id}/`, `GET /api/health/`.
- book-service: `GET/POST /api/books/`, `GET/PUT/DELETE /api/books/{book_id}/`, `GET /api/health/`.
- cart-service: `GET /api/carts/customer/{customer_id}/`, `POST /api/carts/customer/{customer_id}/items/`, `PUT /api/carts/items/{item_id}/`, `DELETE /api/carts/items/{item_id}/`, `DELETE /api/carts/customer/{customer_id}/clear/`, `GET /api/health/`.
- order-service: `GET /api/orders/` (manager list), `POST /api/orders/`, `GET /api/orders/{order_id}/`, `GET /api/orders/customer/{customer_id}/`, `GET /api/health/`.
- ship-service: `GET /api/shipments/{shipment_id}/`, `GET /api/shipments/order/{order_id}/`, `GET /api/health/`.
- pay-service: `GET /api/payments/{payment_id}/`, `GET /api/payments/order/{order_id}/`, `GET /api/health/`.
- comment-rate-service: `POST /api/reviews/`, `GET /api/reviews/book/{book_id}/`, `GET /api/reviews/customer/{customer_id}/`, `GET /api/reviews/book/{book_id}/average/`, `GET /api/reviews/books/summary/averages/`, `GET /api/health/`.
- recommender-ai-service: `GET /api/recommendations/customer/{customer_id}/`, optional `?limit=`, `GET /api/health/`.

## Internal-Only Endpoints (service-to-service)
- book-service: `GET /internal/books/{book_id}/` (lightweight existence/inventory snapshot).
- cart-service: `POST /internal/carts/auto-create/` (create empty cart for new customer), `GET /internal/carts/customer/{customer_id}/for-order/` (cart snapshot before order).
- order-service: `GET /internal/orders/customer/{customer_id}/history/` (purchase history for recommendations).
- pay-service: `POST /internal/payments/` (create payment record when order is placed).
- ship-service: `POST /internal/shipments/` (create shipment record when order is placed).

## Inter-Service Calls (high level)
- `api-gateway` proxies all external traffic to the correct service; health checks stay local.
- `customer-service` calls cart-service `/internal/carts/auto-create/` after successful registration.
- `cart-service` validates books by calling book-service `/internal/books/{book_id}/` on add/update.
- `order-service` pulls cart data via `/internal/carts/customer/{customer_id}/for-order/`, then triggers `pay-service` and `ship-service` internal create endpoints; it also clears the cart best-effort.
- `recommender-ai-service` pulls purchase history from `order-service` internal history, book catalog from `book-service`, and rating aggregates from `comment-rate-service` to build recommendations.
