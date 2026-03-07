# 10-Minute Demo Plan
Concise, repeatable flow for graders. Assume fresh `docker-compose up --build`.

## Checklist (before recording)
- Ensure `.env` exists (copy `.env.example`).
- Run `docker-compose up --build` and wait for health endpoints to return 200.
- Prepare a REST client (curl/Postman) pointing to `localhost` ports.

## Recommended Demo Order (≈10 minutes)
1. Health tour: hit `/api/health/` on a couple of services and via `api-gateway` to show liveness.
2. Catalog setup: create a category `POST http://localhost:8084/api/catalog/categories/` then list categories.
3. Book setup: create a book `POST http://localhost:8085/api/books/` referencing the category.
4. Customer journey: register a customer `POST http://localhost:8083/api/customers/register/` (auto-creates cart), then login.
5. Cart flow: add an item `POST http://localhost:8086/api/carts/customer/{customer_id}/items/` and show validation against book-service; view cart.
6. Order flow: place order `POST http://localhost:8087/api/orders/`; show resulting payment (`/api/payments/order/{order_id}/`) and shipment (`/api/shipments/order/{order_id}/`).
7. Reviews: add a review `POST http://localhost:8090/api/reviews/`; show average `/api/reviews/book/{book_id}/average/`.
8. Recommendations: call `http://localhost:8091/api/recommendations/customer/{customer_id}/` to show combined logic.
9. Gateway proof: repeat one call through `http://localhost:8080/api/gateway/...` to confirm proxying.

## Sample Data (quick copy)
- Category: `{ "name": "Computer Science", "description": "CS books" }`
- Book: `{ "title": "Clean Code", "isbn": "9780132350884", "author": "Robert C. Martin", "publisher": "Prentice Hall", "price": "120.00", "stock": 5, "category_id": <category_id> }`
- Customer: `{ "full_name": "Ada Lovelace", "email": "ada@example.com", "password": "P@ssw0rd!", "phone": "123456789", "address": "42 Binary Rd" }`
- Review: `{ "customer_id": <customer_id>, "book_id": <book_id>, "rating": 5, "comment": "Great read" }`
- Order payload: `{ "customer_id": <customer_id>, "payment_method": "COD", "shipping_method": "STANDARD", "shipping_address": "42 Binary Rd", "shipping_fee": 2.5 }`

## Key APIs to Show (one per service)
- Catalog: `POST /api/catalog/categories/`
- Book: `POST /api/books/`
- Customer: `POST /api/customers/register/`
- Cart: `POST /api/carts/customer/{customer_id}/items/`
- Order: `POST /api/orders/`
- Payment: `GET /api/payments/order/{order_id}/`
- Shipment: `GET /api/shipments/order/{order_id}/`
- Review: `POST /api/reviews/`
- Recommendation: `GET /api/recommendations/customer/{customer_id}/`
- Gateway: any `/api/gateway/<service>/...` call (e.g., books list)

## Fallbacks if a Service Misbehaves
- If catalog/book is down: show stub data in the request payload and explain dependency; skip cart/order creation.
- If cart is down: demonstrate order creation with a manually crafted payload showing expected structure.
- If payment or shipment is down: still create the order and highlight graceful error handling in responses/logs.
- If recommender is down: show rating averages endpoint as evidence for future recommendations.
