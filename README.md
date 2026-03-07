# BookStore Microservices (Django REST)

Academic 12-service BookStore system built with Django REST Framework. Each service is independent with its own database; communication is REST over HTTP only and proxied externally through `api-gateway`.

## Services & Ports (host:container)
| Service | Host Port | Responsibility |
| --- | --- | --- |
| api-gateway | 8080:8000 | Thin REST proxy |
| staff-service | 8081:8000 | Staff accounts |
| manager-service | 8082:8000 | Managers & dashboard |
| customer-service | 8083:8000 | Customers & profiles |
| catalog-service | 8084:8000 | Categories |
| book-service | 8085:8000 | Books & inventory |
| cart-service | 8086:8000 | Shopping cart |
| order-service | 8087:8000 | Orders lifecycle |
| ship-service | 8088:8000 | Shipments |
| pay-service | 8089:8000 | Payments |
| comment-rate-service | 8090:8000 | Reviews & ratings |
| recommender-ai-service | 8091:8000 | Rule-based recommendations |

## Quick Start
```bash
cp .env.example .env    # optional; compose sets sensible defaults
docker-compose up --build
```
All services will start with dedicated Postgres containers. Default service URLs inside the network use service names (e.g., `http://book-service:8000`).

### Database Init at Startup
Each service image includes `start.sh`, which runs `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL host without pre-baked migration files.

## Repository Layout
```
api-gateway/                # proxy
book-service/               # books CRUD + internal validator
cart-service/               # carts and items
catalog-service/            # categories
comment-rate-service/       # reviews & averages
customer-service/           # customers + auto-cart creation
manager-service/            # managers + dashboard summary
order-service/              # orders + payment & shipment orchestration
pay-service/                # payments
recommender-ai-service/     # rule-based recommendations
ship-service/               # shipments
staff-service/              # staff accounts
docs/architecture|api|demo|report
postman/                    # collections (placeholders)
docker-compose.yml
.gitignore
README.md
```

## Documentation
- Per-service README files describe endpoints, env vars, setup, and curl examples.
- Additional notes live under `docs/`.

## Cleanup
`.gitignore` excludes venv, __pycache__, pyc, db.sqlite3, and other artifacts to keep the repo clean.
