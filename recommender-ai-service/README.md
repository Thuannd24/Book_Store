# recommender-ai-service

Rule-based recommendation microservice for BookStore.

## Environment Variables
| Name | Default | Description |
| --- | --- | --- |
| SECRET_KEY | change-me-to-a-random-secret | Django secret key |
| DEBUG | False | Enable Django debug |
| ALLOWED_HOSTS | * | Allowed hosts |
| DATABASE_URL | sqlite:///db.sqlite3 | Not required, kept for compatibility |
| ORDER_SERVICE_URL | http://order-service:8000 | Base URL for order-service (purchase history) |
| BOOK_SERVICE_URL | http://book-service:8000 | Base URL for book-service (catalog) |
| REVIEW_SERVICE_URL | http://comment-rate-service:8000 | Base URL for comment-rate-service (ratings) |

## Run Locally
1. `cd recommender-ai-service/app`
2. `python -m venv .venv && .\\.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `copy ..\\.env.example .env`
5. `python manage.py migrate`  # no models, but keeps Django happy
6. `python manage.py runserver 0.0.0.0:8000`

## Run Tests
`cd recommender-ai-service/app && python manage.py test`

## Docker
`docker build -t recommender-ai-service .`

`docker run --env-file .env -p 8091:8000 recommender-ai-service`

## API
- GET /api/recommendations/customer/{customer_id}/
- GET /api/health/

### Sample Requests
Get recommendations  
```bash
curl http://localhost:8091/api/recommendations/customer/1/
```

Limit to top 3  
```bash
curl "http://localhost:8091/api/recommendations/customer/1/?limit=3"
```

Health  
```bash
curl http://localhost:8091/api/health/
```

### Recommendation Logic
1) Fetch purchase history from order-service (`/internal/orders/customer/{id}/history/`) to learn purchased book IDs and derive preferred categories.  
2) Fetch all books from book-service (`/api/books/`). Filter to ACTIVE and `stock > 0`, exclude already purchased books.  
3) Fetch average ratings from comment-rate-service (`/api/reviews/books/summary/averages/`).  
4) Score candidates: +5 for matching a preferred category (or +1 when no history), +average_rating, +0.02 per unit stock (capped at 50). Reasons note category/rating/stock.  
5) Sort by score (then rating, stock, id) and return top N (default 5).

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
