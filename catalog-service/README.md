# catalog-service

Django REST Framework microservice that manages book categories.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/catalog_db | PostgreSQL URL (falls back to sqlite) |

## Run Locally
1. `cd catalog-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd catalog-service/app && python manage.py test`

## Docker
`docker build -t catalog-service .`

`docker run --env-file .env -p 8084:8000 catalog-service`

## API Quick Reference
- GET  /api/catalog/categories/
- POST /api/catalog/categories/
- GET  /api/catalog/categories/{category_id}/
- PUT  /api/catalog/categories/{category_id}/
- DELETE /api/catalog/categories/{category_id}/
- GET  /api/health/

## Sample Requests
Create category  
```bash
curl -X POST http://localhost:8084/api/catalog/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Software Engineering", "description": "SE books"}'
```

List categories  
```bash
curl http://localhost:8084/api/catalog/categories/
```

Update category  
```bash
curl -X PUT http://localhost:8084/api/catalog/categories/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Software Eng", "slug": "", "description": "updated"}'
```

Delete category  
```bash
curl -X DELETE http://localhost:8084/api/catalog/categories/1/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
