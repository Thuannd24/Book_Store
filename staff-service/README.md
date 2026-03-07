# staff-service

Django REST Framework microservice that manages staff identities for demo/admin purposes.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/staff_db | PostgreSQL URL (falls back to sqlite) |

## Run Locally
1. `cd staff-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd staff-service/app && python manage.py test`

## Docker
`docker build -t staff-service .`

`docker run --env-file .env -p 8081:8000 staff-service`

## API Quick Reference
- POST /api/staff/register/
- POST /api/staff/login/
- GET  /api/staff/{staff_id}/
- GET  /api/staff/
- GET  /api/health/

## Sample Requests
Register  
```bash
curl -X POST http://localhost:8081/api/staff/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "staff_code": "S001",
    "full_name": "Alice Admin",
    "email": "alice@example.com",
    "password": "secret123",
    "role": "admin",
    "department": "IT"
  }'
```

Login  
```bash
curl -X POST http://localhost:8081/api/staff/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "secret123"}'
```

Get profile  
```bash
curl http://localhost:8081/api/staff/1/
```

List staff  
```bash
curl http://localhost:8081/api/staff/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
