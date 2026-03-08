# Architecture Justification – BookStore Microservices (Assignment 06)

## 1. Why Microservices Over a Monolith

The BookStore application was decomposed into microservices for the following reasons:

- **Independent deployability**: Each service (catalog, orders, payments, shipping) can be deployed, scaled, and updated independently without downtime to the rest of the system.
- **Technology isolation**: Individual teams can choose the right data store and libraries per domain (e.g., a recommendation service using ML libraries does not affect the core order flow).
- **Fault isolation**: A failure in the `recommender-ai-service` does not bring down the checkout flow.
- **Scalability**: High-traffic services (e.g., `book-service`, `cart-service`) can be scaled horizontally while low-traffic services remain small.

**Trade-offs acknowledged**: Distributed systems introduce operational complexity (network latency, partial failures, distributed tracing). These are mitigated by the patterns described below.

---

## 2. JWT Authentication Design – Central `auth-service`

### Decision: Central auth-service vs per-service validation

We chose a **central `auth-service`** rather than embedding JWT validation in every service:

| Factor | Central auth-service | Per-service |
|---|---|---|
| Key rotation | Single place to update signing key | Must update all services |
| Blacklisting / logout | Maintained in one store | Requires shared cache or DB |
| Consistency | One source of truth | Risk of drift |
| Latency | One extra HTTP call per request at gateway | Inline (faster) |

The API gateway calls `POST /auth/token/verify/` for every authenticated request, adds `X-User-Id` and `X-User-Role` headers, and forwards the enriched request downstream. Downstream services trust these headers because they are only reachable from the internal Docker network.

### Token structure

```json
{
  "user_id": 42,
  "email": "user@example.com",
  "role": "CUSTOMER",
  "exp": "<60 minutes from now>"
}
```

- **Access token** lifetime: 60 minutes (short to limit blast radius of token theft).
- **Refresh token** lifetime: 7 days (stored client-side, sent only to `/auth/token/refresh/`).
- **Algorithm**: HS256 with a strong signing key from environment variable `JWT_SECRET_KEY`.
- **Blacklisting**: Logout blacklists the refresh token via `djangorestframework-simplejwt`'s built-in blacklist app.

### Feature flag

`JWT_AUTH_ENABLED` defaults to `false` so existing integration tests and local development pass without running `auth-service`. Set to `true` in production.

---

## 3. Saga Pattern – Orchestration vs Choreography

### Why the Saga pattern?

Order creation spans three services (order-service, pay-service, ship-service). A simple sequential REST call with no rollback leaves orphaned payments when shipping fails.

### Orchestration (chosen) vs Choreography

| Factor | Orchestration (chosen) | Choreography |
|---|---|---|
| Visibility | Single saga class has the full workflow | Logic is spread across event handlers |
| Debugging | One log trail per saga | Must correlate events across services |
| Complexity | Moderate | High for cross-service rollback |
| Coupling | Orchestrator knows services | Services react to events (looser) |

We chose **orchestration** because the order creation workflow is deterministic and linear. The `OrderSaga` class in `order-service/app/orders/saga.py` drives the following steps:

```
CREATE_ORDER → RESERVE_PAYMENT → RESERVE_SHIPPING → CONFIRM_ORDER
```

### Compensation logic

| Failure point | Compensation |
|---|---|
| `RESERVE_PAYMENT` fails | Mark order `FAILED` |
| `RESERVE_SHIPPING` fails | Cancel payment (`DELETE /internal/payments/{id}/`), mark order `COMPENSATED` |
| `CONFIRM_ORDER` fails | Cancel both payment and shipment, mark order `COMPENSATED` |

### SagaLog model

Every step transition is recorded in the `saga_logs` table, enabling post-mortem analysis and idempotent replay.

---

## 4. RabbitMQ vs Kafka

We selected **RabbitMQ** over Kafka for the following reasons:

| Factor | RabbitMQ | Kafka |
|---|---|---|
| Setup complexity | Low (single container) | High (ZooKeeper/KRaft + broker) |
| Message model | Queue / topic exchange (AMQP) | Partitioned log |
| At-this-scale fit | Excellent | Over-engineered |
| Django ecosystem | `pika` library, well-documented | `confluent-kafka` or `aiokafka` |
| Management UI | Built-in web UI at port 15672 | Needs separate tool (Kafdrop, etc.) |

For an academic microservices project processing hundreds (not millions) of messages per day, RabbitMQ is the pragmatic choice. Events published include `order.created`, `order.confirmed`, `order.failed`, and `order.compensated` on the `orders` topic exchange.

---

## 5. API Gateway Responsibilities

The `api-gateway` acts as the single entry point for all client requests:

1. **Routing**: Maps `/api/gateway/<service>/<path>` to the correct downstream service URL.
2. **JWT validation** (when `JWT_AUTH_ENABLED=true`): Calls `auth-service` to verify the Bearer token, then injects `X-User-Id` and `X-User-Role` into downstream headers.
3. **Rate limiting**: 100 requests/minute per IP using Django cache (Redis in production, LocMem in dev). Controlled by `RATE_LIMIT_ENABLED`.
4. **Request logging**: Structured JSON logs via `RequestLoggingMiddleware` (method, path, status, duration_ms, user_id, role).
5. **Auth proxy**: `/api/gateway/auth/*` forwards directly to `auth-service` (login, token refresh, logout are skipped from JWT check).
6. **Metrics endpoint**: `GET /api/metrics/` returns uptime and version.

---

## 6. Observability Strategy

### Health checks

Every service exposes `GET /api/health/` returning:

```json
{
  "status": "ok | degraded",
  "service": "<service-name>",
  "db": "ok | error",
  "version": "2.0.0"
}
```

HTTP 200 when healthy, 503 when degraded (DB unreachable). Docker Compose health checks poll these endpoints.

### Structured logging

The API gateway emits one JSON log line per request:

```json
{"method": "POST", "path": "/api/gateway/orders/orders/", "status": 201, "duration_ms": 145.3, "ip": "10.0.0.1", "user_id": 42, "role": "CUSTOMER"}
```

### RabbitMQ management UI

Browse `http://localhost:15672` (user: `bookstore`, password: `bookstore123`) to inspect queue depths, message rates, and unacked messages.

### Future improvements

- Integrate Prometheus + Grafana for metric dashboards.
- Add distributed tracing via OpenTelemetry (trace IDs propagated via `X-Trace-Id` headers).
- Set up Loki for log aggregation.

---

## 7. Fault Simulation Guide

See `docs/fault-simulation.md` for step-by-step instructions on simulating partial failures and verifying compensation.

---

## 8. Load Testing Examples

### Using wrk

```bash
# 30-second load test: 10 threads, 100 connections
wrk -t10 -c100 -d30s http://localhost:8080/api/health/
```

### Using Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class BookStoreUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def browse_books(self):
        self.client.get("/api/gateway/books/books/")

    @task(3)
    def view_book(self):
        self.client.get("/api/gateway/books/books/1/")
```

```bash
locust -f locustfile.py --host=http://localhost:8080 --users 50 --spawn-rate 5
```

Expected results at 50 concurrent users: < 200 ms p95 latency for read endpoints, < 500 ms p95 for order creation (involves 3 service calls).
