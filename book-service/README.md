# book-service

Django REST Framework microservice that owns book data and exposes public CRUD plus an internal contract for other services.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug mode |
| ALLOWED_HOSTS | * | Comma-separated allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/book_db | PostgreSQL connection string (falls back to sqlite if unset) |

## Run Locally
1. `cd book-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`  (or use your preferred virtualenv)
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`  (or `cp ../.env.example .env` on macOS/Linux)
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd book-service/app && python manage.py test`

## Docker
`docker build -t book-service .`

`docker run --env-file .env -p 8085:8000 book-service`

## API Quick Reference
- GET /api/books/?category_id=...&keyword=...
- GET /api/books/{book_id}/
- POST /api/books/
- PUT /api/books/{book_id}/
- DELETE /api/books/{book_id}/
- GET /internal/books/{book_id}/
- GET /api/health/

## Curl Examples
Base URL assumes `http://localhost:8085`.

List books filtered by category  
```bash
curl "http://localhost:8085/api/books/?category_id=2"
```

Create a book  
```bash
curl -X POST http://localhost:8085/api/books/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code",
    "isbn": "9780132350884",
    "author": "Robert C. Martin",
    "publisher": "Prentice Hall",
    "price": "120.00",
    "stock": 5,
    "description": "A handbook of agile software craftsmanship.",
    "image_url": "http://example.com/clean-code.jpg",
    "category_id": 2,
    "category_name_snapshot": "Software Engineering",
    "status": "ACTIVE"
  }'
```

Update a book  
```bash
curl -X PUT http://localhost:8085/api/books/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Clean Code (2nd Ed)",
    "isbn": "9780132350884",
    "author": "Robert C. Martin",
    "publisher": "Prentice Hall",
    "price": "125.00",
    "stock": 3,
    "description": "Updated edition.",
    "image_url": "http://example.com/clean-code-2.jpg",
    "category_id": 2,
    "category_name_snapshot": "Software Engineering",
    "status": "ACTIVE"
  }'
```

Internal contract for other services  
```bash
curl http://localhost:8085/internal/books/1/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
