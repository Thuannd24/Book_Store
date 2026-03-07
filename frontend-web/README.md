# BookStore Frontend

React + Vite + Tailwind CSS frontend for the BookStore Microservices academic project.

## Tech Stack

| Tool | Version | Role |
|---|---|---|
| React | 18 | UI framework |
| Vite | 7 | Build tool & dev server |
| Tailwind CSS | v4 | Utility-first styling |
| React Router | v6 | Client-side routing |
| Axios | – | HTTP client with interceptors |

## Prerequisites

- **Node.js 18+** — for running the frontend dev server
- **Docker & Docker Compose** — for running all backend microservices

## Quick Start

### 1. Start the backend

```bash
# From the project root
docker-compose up -d
```

Wait ~30 seconds for all services to become healthy. The API gateway will be available at **http://localhost:8080**.

### 2. Start the frontend

```bash
cd frontend-web
npm install
cp .env.example .env   # edit if your gateway runs on a different port
npm run dev
```

Open **http://localhost:3000**

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8080` | API Gateway base URL |

## Demo Flow

### As a Customer

1. Open **http://localhost:3000**
2. Browse the homepage — featured books and categories load automatically
3. Go to `/register` — create an account
4. Go to `/login` — sign in
5. Browse `/books` — search by keyword or filter by category (desktop sidebar or mobile dropdown)
6. Click a book — view detail, adjust quantity, click **Add to Cart**
7. Go to `/cart` — review items, adjust quantities
8. Click **Checkout** → `/checkout` — fill address and payment method, place order
9. Go to `/orders` — view order history; click an order for detail view
10. Go to `/reviews` — select a book, rate it, write a comment
11. Go to `/recommendations` — see AI-powered suggestions (requires purchase history)

### As Staff

1. Go to `/staff/login` — sign in with a staff account
2. `/staff/books` — Add, edit, delete books (modal form with validation)
3. `/staff/categories` — Add, edit, delete categories (name auto-generates slug)

### As Manager

1. Go to `/manager/login` — sign in with a manager account
2. `/manager/dashboard` — four stat cards: Customers, Books, Orders, Reviews
   - Cards show ⚠ notes if a downstream service is unavailable

## Pages

### Customer

| Route | Description | Auth |
|---|---|---|
| `/` | Home — hero, category grid, featured books | Public |
| `/register` | Customer registration | Public |
| `/login` | Customer login | Public |
| `/books` | Book list with keyword search + category filter | Public |
| `/books/:id` | Book detail — info, add-to-cart, customer reviews | Public |
| `/cart` | Shopping cart with quantity controls | Login required |
| `/checkout` | Shipping & payment form, order summary | Login required |
| `/orders` | Order history list | Login required |
| `/orders/:id` | Single order detail | Login required |
| `/reviews` | Submit reviews; view past reviews with book titles | Login required |
| `/recommendations` | AI-powered recommendations | Login required |

### Staff

| Route | Description | Auth |
|---|---|---|
| `/staff/login` | Staff login | Public |
| `/staff/books` | Book CRUD — table with search, modal form | Staff login |
| `/staff/categories` | Category CRUD — table, auto-slug, active toggle | Staff login |

### Manager

| Route | Description | Auth |
|---|---|---|
| `/manager/login` | Manager login | Public |
| `/manager/dashboard` | Summary stats — Customers, Books, Orders, Reviews | Manager login |

## API Endpoints Consumed

All calls go through the API gateway at port 8080 via the pattern:
`/api/gateway/{service_key}/api/{service_path}`

| Service Key | Endpoints Used |
|---|---|
| `customers` | `POST /api/customers/register/`, `POST /api/customers/login/`, `GET /api/customers/{id}/` |
| `books` | `GET/POST /api/books/`, `GET/PUT/DELETE /api/books/{id}/` |
| `catalog` | `GET/POST /api/catalog/categories/`, `GET/PUT/DELETE /api/catalog/categories/{id}/` |
| `carts` | `GET /api/carts/customer/{id}/`, `POST /api/carts/customer/{id}/items/`, `PUT/DELETE /api/carts/items/{id}/`, `DELETE /api/carts/customer/{id}/clear/` |
| `orders` | `POST /api/orders/`, `GET /api/orders/{id}/`, `GET /api/orders/customer/{id}/` |
| `reviews` | `POST /api/reviews/`, `GET /api/reviews/book/{id}/`, `GET /api/reviews/book/{id}/average/`, `GET /api/reviews/customer/{id}/` |
| `recommendations` | `GET /api/recommendations/customer/{id}/` |
| `staff` | `POST /api/staff/login/` |
| `managers` | `POST /api/managers/login/`, `GET /api/manager/dashboard/summary/` |

## Authentication

The backend returns a user object on login — there is no JWT. The frontend stores the object in `localStorage` under the key `customer`, `staff`, or `manager`. Protected routes redirect to the appropriate login page if the key is absent.

**No session expiry is implemented.** Clear localStorage to force logout.

## Known API Mismatches / Notes

| Issue | Detail |
|---|---|
| No JWT | Session is plain localStorage object; no token refresh or expiry |
| Dashboard `recent_orders` | The summary endpoint does not return recent orders; the table section shows a placeholder message |
| Recommendations cold start | New users with no purchase history receive empty recommendations — handled with an EmptyState |
| Duplicate reviews | The backend does not prevent a customer reviewing the same book twice |
| `category_name_snapshot` | Books store a snapshot of the category name at creation; changing the category name later will not update the snapshot |

## Production Build

```bash
npm run build      # outputs to dist/
npm run preview    # serve the dist/ locally
```

