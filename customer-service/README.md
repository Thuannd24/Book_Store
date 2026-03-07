# customer-service

Manages customer accounts for the BookStore platform.

## Responsibilities
- Customer registration (with auto-cart creation via cart-service)
- Customer login (credential validation)
- Customer profile retrieval and update
- Internal lookup endpoint for other services

## Port
Runs on port **8000** inside Docker (mapped to **8083** on the host).

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | `change-me` | Django secret key |
| `DEBUG` | ❌ | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | ❌ | `*` | Comma-separated allowed hosts |
| `DATABASE_URL` | ✅ | `sqlite:///db.sqlite3` | PostgreSQL connection string |
| `CART_SERVICE_URL` | ❌ | `http://cart-service:8000` | Base URL of cart-service |

---

## Running Locally

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r app/requirements.txt

# 3. Configure environment
cp .env.example app/.env
# Edit app/.env and set DATABASE_URL, SECRET_KEY, etc.

# 4. Run database migrations
python app/manage.py makemigrations customers
python app/manage.py migrate

# 5. Start development server
python app/manage.py runserver 8083
```

## Running with Docker

```bash
docker build -t customer-service .
docker run -p 8083:8000 --env-file .env customer-service
```

---

## API Reference

### Health Check

```bash
curl http://localhost:8083/api/health/
```
**Response:**
```json
{"status": "ok", "service": "customer-service"}
```

---

### Register a Customer

```bash
curl -X POST http://localhost:8083/api/customers/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Nguyen Van A",
    "email": "vana@example.com",
    "password": "secret123",
    "phone": "0901234567",
    "address": "123 Le Loi, Ho Chi Minh City"
  }'
```
**Success Response (201):**
```json
{
  "id": 1,
  "full_name": "Nguyen Van A",
  "email": "vana@example.com",
  "phone": "0901234567",
  "address": "123 Le Loi, Ho Chi Minh City",
  "is_active": true,
  "created_at": "2026-03-07T14:00:00Z",
  "updated_at": "2026-03-07T14:00:00Z",
  "cart_created": true
}
```
**When cart-service is unavailable (still 201):**
```json
{
  "id": 2,
  ...
  "cart_created": false,
  "warning": "Customer registered but cart creation failed: cart-service is unreachable"
}
```

---

### Login

```bash
curl -X POST http://localhost:8083/api/customers/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vana@example.com",
    "password": "secret123"
  }'
```
**Success Response (200):**
```json
{
  "id": 1,
  "full_name": "Nguyen Van A",
  "email": "vana@example.com",
  "phone": "0901234567",
  "address": "123 Le Loi, Ho Chi Minh City",
  "is_active": true,
  "created_at": "2026-03-07T14:00:00Z",
  "updated_at": "2026-03-07T14:00:00Z"
}
```

---

### Get Customer Profile

```bash
curl http://localhost:8083/api/customers/1/
```
**Response (200):**
```json
{
  "id": 1,
  "full_name": "Nguyen Van A",
  "email": "vana@example.com",
  "phone": "0901234567",
  "address": "123 Le Loi, Ho Chi Minh City",
  "is_active": true,
  "created_at": "2026-03-07T14:00:00Z",
  "updated_at": "2026-03-07T14:00:00Z"
}
```

---

### Update Customer Profile

```bash
curl -X PUT http://localhost:8083/api/customers/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Nguyen Van A (Updated)",
    "phone": "0999888777",
    "address": "456 Hai Ba Trung, Ha Noi"
  }'
```
**Response (200):** Updated customer profile.

---

### Internal: Get Customer (for other services)

```bash
curl http://localhost:8083/internal/customers/1/
```
**Response (200):**
```json
{
  "id": 1,
  "full_name": "Nguyen Van A",
  "email": "vana@example.com",
  "phone": "0901234567",
  "address": "123 Le Loi, Ho Chi Minh City",
  "is_active": true
}
```

---

## Data Model

```
customers table
├── id            BigAutoField (PK)
├── full_name     CharField(255)
├── email         EmailField (unique)
├── password_hash CharField(255)     # SHA-256 of raw password
├── phone         CharField(20)
├── address       TextField
├── is_active     BooleanField       # default True
├── created_at    DateTimeField      # auto
└── updated_at    DateTimeField      # auto
```

## Inter-service Interactions

| Direction | Target | Endpoint | When |
|---|---|---|---|
| ➡️ OUT | `cart-service` | `POST /internal/carts/auto-create/` | After successful registration |
| ⬅️ IN | `comment-rate-service` | — | Calls `GET /internal/customers/{id}/` to validate customer |

## Migrations

```bash
python app/manage.py makemigrations customers
python app/manage.py migrate
```

## Container Startup
The Docker container runs `start.sh`, which calls `python manage.py makemigrations --noinput` and `python manage.py migrate --noinput` before launching gunicorn. This keeps `docker-compose up --build` usable on a clean PostgreSQL instance.
