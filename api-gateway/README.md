# api-gateway

Thin Django REST Framework gateway that proxies client requests to domain services.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | sqlite:///db.sqlite3 | Not really used, present for Django |
| CUSTOMER_SERVICE_URL | http://customer-service:8000 | customer-service base URL |
| BOOK_SERVICE_URL | http://book-service:8000 | book-service base URL |
| CART_SERVICE_URL | http://cart-service:8000 | cart-service base URL |
| ORDER_SERVICE_URL | http://order-service:8000 | order-service base URL |
| REVIEW_SERVICE_URL | http://comment-rate-service:8000 | comment-rate-service base URL |
| RECOMMENDER_SERVICE_URL | http://recommender-ai-service:8000 | recommender service base URL |
| CATALOG_SERVICE_URL | http://catalog-service:8000 | catalog-service base URL |
| STAFF_SERVICE_URL | http://staff-service:8000 | staff-service base URL |
| MANAGER_SERVICE_URL | http://manager-service:8000 | manager-service base URL |

## Run Locally
1. `cd api-gateway/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd api-gateway/app && python manage.py test`

## Docker
`docker build -t api-gateway .`

`docker run --env-file .env -p 8080:8000 api-gateway`

## Gateway Routes
- `/api/gateway/customers/...` â†’ CUSTOMER_SERVICE_URL
- `/api/gateway/books/...` â†’ BOOK_SERVICE_URL
- `/api/gateway/carts/...` â†’ CART_SERVICE_URL
- `/api/gateway/orders/...` â†’ ORDER_SERVICE_URL
- `/api/gateway/reviews/...` â†’ REVIEW_SERVICE_URL
- `/api/gateway/recommendations/...` â†’ RECOMMENDER_SERVICE_URL
- `/api/gateway/catalog/...` â†’ CATALOG_SERVICE_URL
- `/api/gateway/staff/...` â†’ STAFF_SERVICE_URL
- `/api/gateway/managers/...` â†’ MANAGER_SERVICE_URL
- Health: `/api/health/`

## Curl Examples
Health  
```bash
curl http://localhost:8080/api/health/
```

Proxy customer registration  
```bash
curl -X POST http://localhost:8080/api/gateway/customers/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"a@b.com","password":"secret"}'
```

Proxy book list  
```bash
curl "http://localhost:8080/api/gateway/books/?keyword=python"
```

Proxy order creation (example payload)  
```bash
curl -X POST http://localhost:8080/api/gateway/orders/ \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"payment_method":"CARD","shipping_method":"STANDARD","shipping_address":"123 Main","shipping_fee":2.5}'
```

Proxy review average  
```bash
curl http://localhost:8080/api/gateway/reviews/book/1/average/
```

Proxy recommendations  
```bash
curl http://localhost:8080/api/gateway/recommendations/customer/1/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
