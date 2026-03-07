# Architecture Overview
Django REST microservices, each owning a narrow domain and its own PostgreSQL database. Services communicate synchronously over HTTP inside the Docker network; no shared code or shared databases.

## Why Microservices (for this assignment)
- Aligns bounded contexts: staff, managers, customers, catalog, books, cart, order, payment, shipment, reviews, recommendations, gateway.
- Independent deployability: one service can be rebuilt without touching others.
- Fault isolation: a failing downstream returns an error to the caller without collapsing the whole stack.
- Database-per-service avoids cross-team coupling and enforces API contracts.

## Service Responsibilities (one database each)
- api-gateway: proxy and API aggregation only; no business logic.
- staff-service: staff auth + directory.
- manager-service: manager auth + dashboard summary.
- customer-service: customer auth/profile and auto-cart trigger.
- catalog-service: category CRUD.
- book-service: book CRUD + inventory snapshot for validators.
- cart-service: cart and cart items lifecycle.
- order-service: order orchestration and history.
- pay-service: record payments for orders.
- ship-service: record shipments for orders.
- comment-rate-service: reviews and rating aggregates.
- recommender-ai-service: rule-based recommendations from history + ratings.

## Database-Per-Service Explanation
Each service connects to its own Postgres instance (see `docker-compose.yml`). No cross-database joins. Data needed from another domain is retrieved via HTTP and stored as snapshots (e.g., book title/price in cart/order payloads). This keeps schemas decoupled and simplifies grading on fresh databases.

## Request Flow Examples
- Customer register → auto cart: `customer-service` accepts registration, then POSTs to `cart-service` `/internal/carts/auto-create/` to create an empty cart for that customer.
- Add to cart → validate book: `cart-service` validates book existence/stock by calling `book-service` `/internal/books/{book_id}/` before writing the cart item.
- Create order → payment + shipment: `order-service` pulls cart snapshot via `/internal/carts/customer/{customer_id}/for-order/`, creates the order, POSTs to `pay-service` `/internal/payments/` and `ship-service` `/internal/shipments/`, then best-effort clears the cart.
- Recommendation flow: `recommender-ai-service` queries `order-service` `/internal/orders/customer/{customer_id}/history/`, fetches available books from `book-service`, and rating aggregates from `comment-rate-service` to return ranked recommendations.
