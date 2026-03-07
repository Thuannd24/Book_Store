# manager-service

Django REST Framework microservice for manager registration, login, profile lookup, and a lightweight dashboard that aggregates counts from other services.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/manager_db | PostgreSQL URL (falls back to sqlite) |
| CUSTOMER_SERVICE_URL | http://customer-service:8000 | Base URL for customer-service |
| BOOK_SERVICE_URL | http://book-service:8000 | Base URL for book-service |
| ORDER_SERVICE_URL | http://order-service:8000 | Base URL for order-service |
| REVIEW_SERVICE_URL | http://comment-rate-service:8000 | Base URL for comment-rate-service |

## Run Locally
1. `cd manager-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd manager-service/app && python manage.py test`

## Docker
`docker build -t manager-service .`

`docker run --env-file .env -p 8082:8000 manager-service`

## API Quick Reference
- POST /api/managers/register/
- POST /api/managers/login/
- GET  /api/managers/{manager_id}/
- GET  /api/manager/dashboard/summary/
- GET  /api/health/

## Sample Requests
Register manager  
```bash
curl -X POST http://localhost:8082/api/managers/register/ \
  -H "Content-Type: application/json" \
  -d '{"manager_code": "M001", "full_name": "Alice Manager", "email": "alice@example.com", "password": "secret123"}'
```

Login  
```bash
curl -X POST http://localhost:8082/api/managers/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "secret123"}'
```

Profile  
```bash
curl http://localhost:8082/api/managers/1/
```

Dashboard summary  
```bash
curl http://localhost:8082/api/manager/dashboard/summary/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
