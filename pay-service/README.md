# pay-service

Django REST Framework microservice that records payments for orders.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/pay_db | PostgreSQL URL (falls back to sqlite) |

## Run Locally
1. `cd pay-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd pay-service/app && python manage.py test`

## Docker
`docker build -t pay-service .`

`docker run --env-file .env -p 8089:8000 pay-service`

## API Quick Reference
- POST /internal/payments/
- GET /api/payments/{payment_id}/
- GET /api/payments/order/{order_id}/
- GET /api/health/

## Business Rules
- transaction_ref format: `PAY-{order_id}-{seq}` (seq is zero-padded to 3).
- COD -> status PENDING, paid_at null.
- BANK_TRANSFER -> status SUCCESS, paid_at set to now.

## Curl Examples
Create payment (internal)  
```bash
curl -X POST http://localhost:8089/internal/payments/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 100,
    "customer_id": 1,
    "method": "COD",
    "amount": "240.00"
  }'
```

Get payment detail  
```bash
curl http://localhost:8089/api/payments/1/
```

List payments by order  
```bash
curl http://localhost:8089/api/payments/order/100/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
