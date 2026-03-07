# order-service

Django REST Framework microservice that creates orders from carts, calls pay/ship services, and exposes order history.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/order_db | PostgreSQL URL (falls back to sqlite) |
| CART_SERVICE_URL | http://cart-service:8000 | Base URL of cart-service |
| PAY_SERVICE_URL | http://pay-service:8000 | Base URL of pay-service |
| SHIP_SERVICE_URL | http://ship-service:8000 | Base URL of ship-service |

## Run Locally
1) `cd order-service/app`
2) `python -m venv .venv && .\\.venv\\Scripts\\activate`
3) `pip install -r requirements.txt`
4) `copy ..\\.env.example .env`
5) `python manage.py migrate`
6) `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd order-service/app && python manage.py test`

## Docker
`docker build -t order-service .`

`docker run --env-file .env -p 8087:8000 order-service`

## API Quick Reference
- POST /api/orders/
- GET /api/orders/{order_id}/
- GET /api/orders/customer/{customer_id}/
- GET /internal/orders/customer/{customer_id}/history/
- GET /api/health/

## Order Creation Flow
1. Fetch cart snapshot from cart-service `/internal/carts/customer/{customer_id}/for-order/`
2. Create order + order_items (snapshots)
3. Call pay-service `/internal/payments/`
4. Call ship-service `/internal/shipments/`
5. If both succeed → status CONFIRMED; otherwise FAILED
6. Best-effort clear cart via `/api/carts/customer/{customer_id}/clear/`

## Curl Examples
Base URL `http://localhost:8087`.

Create order  
```bash
curl -X POST http://localhost:8087/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "payment_method": "COD",
    "shipping_method": "STANDARD",
    "shipping_address": "123 Main St",
    "shipping_fee": "0.00"
  }'
```

Get order detail  
```bash
curl http://localhost:8087/api/orders/1/
```

List customer orders  
```bash
curl http://localhost:8087/api/orders/customer/1/
```

Purchase history for recommender  
```bash
curl http://localhost:8087/internal/orders/customer/1/history/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
