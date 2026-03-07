# ship-service

Django REST Framework microservice that records shipment requests for orders.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/ship_db | PostgreSQL URL (falls back to sqlite) |

## Run Locally
1. `cd ship-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd ship-service/app && python manage.py test`

## Docker
`docker build -t ship-service .`

`docker run --env-file .env -p 8088:8000 ship-service`

## API Quick Reference
- POST /internal/shipments/
- GET /api/shipments/{shipment_id}/
- GET /api/shipments/order/{order_id}/
- GET /api/health/

## Business Rules
- tracking_code format: `TRK-{order_id}-{seq}` (seq zero-padded to 3).
- Initial status always PENDING.
- Shipping methods: STANDARD, EXPRESS.

## Curl Examples
Create shipment (internal)  
```bash
curl -X POST http://localhost:8088/internal/shipments/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 100,
    "customer_id": 1,
    "shipping_method": "STANDARD",
    "shipping_address": "Ha Noi",
    "shipping_fee": "20.00"
  }'
```

Get shipment detail  
```bash
curl http://localhost:8088/api/shipments/1/
```

List shipments by order  
```bash
curl http://localhost:8088/api/shipments/order/100/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
