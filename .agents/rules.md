# BookStore Microservices — Project Rules

This repository is an **academic Django REST Framework microservices assignment** for a BookStore system.

> Architecture is **frozen**. Do not redesign service boundaries.

---

## Service Map

| Service | Port | Folder | Responsibility |
|---|---|---|---|
| `api-gateway` | 8080 | `api-gateway/` | Routing, auth forwarding, rate-limiting |
| `staff-service` | 8081 | `staff-service/` | Staff account management |
| `manager-service` | 8082 | `manager-service/` | Admin / manager operations |
| `customer-service` | 8083 | `customer-service/` | Customer account management |
| `catalog-service` | 8084 | `catalog-service/` | Categories, publishers, authors |
| `book-service` | 8085 | `book-service/` | Book CRUD & inventory |
| `cart-service` | 8086 | `cart-service/` | Shopping cart |
| `order-service` | 8087 | `order-service/` | Order lifecycle |
| `ship-service` | 8088 | `ship-service/` | Shipping & delivery tracking |
| `pay-service` | 8089 | `pay-service/` | Payment processing |
| `comment-rate-service` | 8090 | `comment-rate-service/` | Reviews & ratings |
| `recommender-ai-service` | 8091 | `recommender-ai-service/` | AI-powered book recommendations |

---

## Hard Rules (Always Follow)

1. **Each service is independent.** No shared code outside a service's own folder.
2. **Each service has its own database.** Each service references its own `DATABASE_URL` environment variable pointing to a dedicated DB.
3. **Communication between services is REST over HTTP only.** Use `requests` library in `services.py`. No message queues, no gRPC, no shared ORM queries.
4. **Never use cross-database foreign keys.** Django `ForeignKey` only within the same service's models.
5. **Store only IDs or snapshots from other services.** Use `IntegerField` or `UUIDField` to reference entities from other services; never import their models.
6. **Work on one service at a time.** Complete and freeze before moving on.
7. **Never modify a service that has already been completed and frozen.** Later services must adapt to existing contracts.
8. **Do not touch unrelated folders.** Only touch the folder of the current service being built.
9. **Keep implementation simple, readable, academic, and Docker-ready.** No overengineering.
10. **Never rename service folders.** The folder names are frozen as listed in the service map above.
11. **Use the fixed REST contracts already defined in the project specification.** Do not invent new endpoints not agreed upon.
12. **Never refactor completed services to support later services.** Later services must adapt.

---

## Required Files Per Service

Every service **must** include these files before it is considered complete:

```
<service-name>/
├── Dockerfile
├── .env.example
├── README.md
└── app/
    ├── requirements.txt
    ├── manage.py
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── <app_name>/
        ├── __init__.py
        ├── admin.py
        ├── apps.py
        ├── models.py
        ├── serializers.py
        ├── views.py
        ├── urls.py
        ├── services.py       # Only if this service calls other services
        └── tests.py
```

---

## Standard File Templates & Conventions

### `requirements.txt` (baseline — extend as needed)
```
django>=4.2,<5.0
djangorestframework>=3.14
django-environ>=0.11
psycopg2-binary>=2.9
gunicorn>=21.2
requests>=2.31          # only if services.py is needed
```

### `Dockerfile` (standard)
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

### `.env.example` (minimum — extend for service-specific vars)
```
SECRET_KEY=change-me-to-a-random-secret
DEBUG=False
ALLOWED_HOSTS=*
DATABASE_URL=postgres://user:password@localhost:5432/<service>_db
```

### `config/settings.py` (standard baseline)
```python
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='change-me')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    '<app_name>',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',   # gateway handles auth
    ],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STATIC_URL = '/static/'
```

### Inter-service calls (`services.py`)
```python
import requests
from django.conf import settings

SERVICE_URL = getattr(settings, 'SOME_SERVICE_URL', 'http://some-service:8000')

def get_resource(resource_id):
    resp = requests.get(f'{SERVICE_URL}/api/resource/{resource_id}/', timeout=5)
    resp.raise_for_status()
    return resp.json()
```

### Health endpoint (always include in `views.py`)
```python
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': '<service-name>'})
```

---

## Code Style Rules

- **Django REST Framework** — always use DRF serializers + views (APIView or ViewSet), never raw Django views.
- **Functionally correct over over-engineered** — no unnecessary abstractions.
- **Minimal but clean service layer** — `services.py` only when calling another service via HTTP.
- **Clear environment variables** — document every env var in `.env.example`.
- **Useful README** — must include:
  - Service description
  - Environment variables table
  - Running locally instructions
  - Curl / API usage examples
  - Migration command

---

## Post-Generation Checklist

After generating any service, perform this review before declaring it done:

- [ ] All imports in `views.py`, `serializers.py`, `services.py` resolve correctly
- [ ] All URL patterns in `urls.py` are wired up in `config/urls.py`
- [ ] Serializers match model fields exactly
- [ ] `tests.py` has at least one test class with a basic CRUD test
- [ ] `Dockerfile` copies correct paths and exposes correct port
- [ ] `requirements.txt` contains all packages actually imported
- [ ] `.env.example` lists every `env(...)` variable referenced in `settings.py`
- [ ] `README.md` includes migration command + at least 3 curl examples
- [ ] No cross-model FK references to other services

---

## REST Contracts (Fixed — Do Not Change)

All inter-service calls must conform to these agreed endpoints:

| Caller | Callee | Endpoint | Purpose |
|---|---|---|---|
| `book-service` | `catalog-service` | `GET /api/categories/{id}/` | Validate category ID |
| `book-service` | `catalog-service` | `GET /api/authors/{id}/` | Validate author ID |
| `book-service` | `catalog-service` | `GET /api/publishers/{id}/` | Validate publisher ID |
| `cart-service` | `book-service` | `GET /api/books/{id}/` | Get book price & stock |
| `order-service` | `cart-service` | `GET /api/cart/{customer_id}/` | Read cart contents |
| `order-service` | `book-service` | `PATCH /api/books/{id}/` | Decrement stock |
| `ship-service` | `order-service` | `GET /api/orders/{id}/` | Get order shipping address |
| `pay-service` | `order-service` | `PATCH /api/orders/{id}/` | Update payment status |
| `comment-rate-service` | `customer-service` | `GET /api/customers/{id}/` | Validate customer |
| `comment-rate-service` | `book-service` | `GET /api/books/{id}/` | Validate book |
| `recommender-ai-service` | `order-service` | `GET /api/orders/?customer_id={id}` | Fetch order history |
| `recommender-ai-service` | `book-service` | `GET /api/books/` | Fetch book catalogue |

---

## Service Implementation Order (Recommended)

Build services in dependency order to avoid blocked inter-service calls:

1. `catalog-service` — no dependencies
2. `staff-service` — no dependencies
3. `manager-service` — no dependencies
4. `customer-service` — no dependencies
5. `book-service` — depends on catalog-service
6. `cart-service` — depends on book-service
7. `order-service` — depends on cart-service, book-service
8. `ship-service` — depends on order-service
9. `pay-service` — depends on order-service
10. `comment-rate-service` — depends on customer-service, book-service
11. `recommender-ai-service` — depends on order-service, book-service
12. `api-gateway` — depends on all services
