# comment-rate-service

Django REST Framework microservice for book reviews and ratings.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | postgres://user:password@localhost:5432/comment_rate_db | PostgreSQL URL (falls back to sqlite) |

## Run Locally
1. `cd comment-rate-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`
5. `python manage.py migrate`
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd comment-rate-service/app && python manage.py test`

## Docker
`docker build -t comment-rate-service .`

`docker run --env-file .env -p 8090:8000 comment-rate-service`

## API Quick Reference
- POST /api/reviews/
- GET  /api/reviews/book/{book_id}/
- GET  /api/reviews/customer/{customer_id}/
- GET  /api/reviews/book/{book_id}/average/
- GET  /api/reviews/books/summary/averages/
- GET  /api/health/

## Sample Requests
Create review  
```bash
curl -X POST http://localhost:8090/api/reviews/ \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1, "customer_id": 2, "rating": 5, "comment": "Great book!"}'
```

List reviews by book  
```bash
curl http://localhost:8090/api/reviews/book/1/
```

Average rating for a book  
```bash
curl http://localhost:8090/api/reviews/book/1/average/
```

Summary averages (all books)  
```bash
curl http://localhost:8090/api/reviews/books/summary/averages/
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
