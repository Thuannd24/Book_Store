# cart-service

Django REST Framework microservice that owns shopping carts and cart items.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug mode |
| ALLOWED_HOSTS | * | Comma-separated allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/cart_db | PostgreSQL connection string (falls back to sqlite if unset) |
| BOOK_SERVICE_URL | http://book-service:8000 | Base URL for book-service internal API |

## Run Locally
1. `cd cart-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`  (or use your preferred virtualenv)
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`  (or `cp ../.env.example .env` on macOS/Linux)
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd cart-service/app && python manage.py test`

## Docker
`docker build -t cart-service .`

`docker run --env-file .env -p 8086:8000 cart-service`

## API Quick Reference
- `POST /internal/carts/auto-create/`
- `GET /api/carts/customer/{customer_id}/`
- `POST /api/carts/customer/{customer_id}/items/`
- `PUT /api/carts/items/{item_id}/`
- `DELETE /api/carts/items/{item_id}/`
- `DELETE /api/carts/customer/{customer_id}/clear/`
- `GET /internal/carts/customer/{customer_id}/for-order/`
- `GET /api/health/`

## Curl Examples
Base URL assumes `http://localhost:8086`.

Auto-create cart  
```bash
curl -X POST http://localhost:8086/internal/carts/auto-create/ \
  -H "Content-Type: application/json" \
  -d '{"customer_id": 1}'
```

Get cart by customer  
```bash
curl http://localhost:8086/api/carts/customer/1/
```

Add item to cart (validates book via book-service)  
```bash
curl -X POST http://localhost:8086/api/carts/customer/1/items/ \
  -H "Content-Type: application/json" \
  -d '{"book_id": 5, "quantity": 2}'
```

Update item quantity  
```bash
curl -X PUT http://localhost:8086/api/carts/items/10/ \
  -H "Content-Type: application/json" \
  -d '{"quantity": 3}'
```

Remove item  
```bash
curl -X DELETE http://localhost:8086/api/carts/items/10/
```

Clear cart  
```bash
curl -X DELETE http://localhost:8086/api/carts/customer/1/clear/
```

Expose cart for order creation  
```bash
curl http://localhost:8086/internal/carts/customer/1/for-order/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
