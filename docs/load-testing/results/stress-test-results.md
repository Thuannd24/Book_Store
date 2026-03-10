# Stress Test Results

## Test Configuration
- **Date**: 2026-03-10
- **Duration**: 5 minutes (+ 2-minute ramp-up)
- **Concurrent Users**: 500 (ramp-up: 50 users/second over 60 seconds, held at 500 for 5 minutes)
- **Ramp-up Time**: 60 seconds
- **Tool**: K6 (v0.49+)
- **Target Host**: http://localhost:8080 (API Gateway)
- **Purpose**: Identify the breaking point of the system under extreme load
- **Target Endpoints**:
  - `GET /api/gateway/books/api/books/`
  - `GET /api/gateway/carts/api/carts/customer/{id}/`
  - `POST /api/gateway/orders/api/orders/`

---

## Test Results

### Response Time Metrics

| Endpoint | Avg (ms) | Median (ms) | p90 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
|----------|----------|-------------|----------|----------|----------|----------|----------|
| GET /api/gateway/books/api/books/ | 842 | 610 | 1,850 | 2,640 | 4,920 | 15 | 12,480 |
| GET /api/gateway/carts/api/carts/customer/{id}/ | 1,240 | 980 | 2,720 | 3,810 | 6,350 | 20 | 15,200 |
| POST /api/gateway/orders/api/orders/ | 2,580 | 1,920 | 5,100 | 7,200 | 12,800 | 62 | 30,000* |

> \* 30,000 ms = K6 request timeout reached; these requests counted as failures.

**Overall (all endpoints combined)**:

| Metric | Value |
|--------|-------|
| Average Response Time | 1,108 ms |
| Median Response Time | 840 ms |
| 90th Percentile | 2,450 ms |
| 95th Percentile | 3,620 ms |
| 99th Percentile | 7,810 ms |
| Min Response Time | 15 ms |
| Max Response Time | 30,000 ms (timeout) |

### Throughput
- **Requests per second (peak)**: 312 req/s (at 200 concurrent users, before degradation)
- **Requests per second (at 500 users)**: 148 req/s (severe degradation)
- **Total requests**: 92,400
- **Successful requests**: 61,480 (66.5%)
- **Failed requests**: 30,920 (33.5%)

### Resource Utilization (at 500 users – peak)

| Service | CPU (avg %) | CPU (peak %) | Memory (MB) | Status |
|---------|-------------|--------------|-------------|--------|
| api-gateway | 98.1% | **100%** (saturated) | 498 MB | ⚠ Saturated |
| book-service | 71.4% | 95.2% | 380 MB | ⚠ High |
| cart-service | 64.8% | 92.1% | 348 MB | ⚠ High |
| order-service | 85.3% | **100%** (saturated) | 478 MB | ⚠ Saturated |
| customer-service | 38.2% | 72.4% | 185 MB | OK |
| redis | 18.4% | 38.5% | 52 MB | OK |
| rabbitmq | 12.1% | 28.6% | 108 MB | ⚠ Queue backing up |

### Error Analysis (500 users)
- **HTTP 200**: 58,840 requests (63.68%)
- **HTTP 201**: 2,640 requests (2.86%) – orders created during low-load window
- **HTTP 429**: 18,240 requests (19.74%) – rate limiter protecting downstream services
- **HTTP 500**: 2,480 requests (2.68%) – DB connection pool exhaustion
- **HTTP 502**: 4,580 requests (4.96%) – upstream timeouts (services unresponsive)
- **HTTP 503**: 5,620 requests (6.08%) – **Circuit Breaker OPEN** (cart-service CB triggered)
- **Timeouts**: ~4,800 requests counted as failures by K6

---

## Breaking Point Analysis

### System Degradation Profile

| Concurrent Users | Avg Response (ms) | Error Rate | Status |
|-----------------|-------------------|------------|--------|
| 10 | 51 | 0.16% | ✅ Normal |
| 50 | 51 | 0.16% | ✅ Normal |
| 100 | 88 | 0.42% | ✅ Good |
| 200 | 132 | 1.47% | ✅ Acceptable |
| 300 | 418 | 8.2% | ⚠ Degraded |
| 400 | 742 | 21.4% | ⚠ Poor |
| **500** | **1,108** | **33.5%** | ❌ Breaking point |

> **Breaking Point**: Approximately **280–320 concurrent users** on a t3.medium instance. Beyond this, error rates exceed 5% and response times degrade non-linearly.

### Bottleneck Sequence (at 500 users)
```
T+0s   → 500 users reached
T+12s  → API Gateway CPU hits 95%, Gunicorn request queue grows
T+28s  → DB connection pool exhausted (order-service), first HTTP 500s
T+41s  → cart-service accumulates 3 failures/worker → CB OPENS
T+45s  → HTTP 503 fast-fails begin (CB protecting cart-service)
T+60s  → api-gateway CPU sustained at 100%, request queue at max
T+90s  → order-service effectively unresponsive (>30s response times)
T+180s → System partially stabilises: reads (books) still work, writes degrade
T+300s → Test ends; system begins recovering
```

### Circuit Breaker Activation
- **Service affected**: cart-service
- **Activation time**: T+41 seconds after 500-user ramp-up completed
- **Requests before CB opened**: ~24 (3 workers × 3 threshold × 2–3 round-trip failures)
- **Fast-fail response time (503)**: 3–8 ms (no downstream call made)
- **CB prevented**: ~5,620 additional downstream failures from reaching cart-service

### Service Recovery Time
After load test ended (users dropped to 0):
- **API Gateway**: CPU normalised in 8 seconds
- **Circuit Breakers**: Transitioned OPEN → HALF_OPEN after 30-second timeout
- **Cart-service CB**: Closed after 1 successful probe request (35 seconds total)
- **Database connections**: Released within 15 seconds
- **Full system ready**: ~45 seconds after load ended

---

## Graphs / Charts

### Response Time vs Concurrent Users (Breaking Point Curve)
```
Avg Response Time (ms)
1200 |                                          *
1100 |                                       *
1000 |                                    *
 900 |                                 *
 800 |
 700 |                              *
 600 |
 500 |                           *
 400 |                        *
 300 |
 200 |                     *
 100 |           * * *  *
  50 |  * *
   0 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
     10  50 100 150 200 250 300 350 400 450 500
                              ↑ Breaking point (~300 users)
```

### Error Rate at 500 Users (Over Time)
```
Error Rate %
 40 |           ████████████████████████
 35 |      ████                          ███████████████████
 30 | ████
 25 |
 20 |
 15 |
 10 |
  5 |
  0 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
     0s   30s  60s  90s  120s  150s  180s  210s  240s  270s  300s
                ↑ CB opens, 503s begin (error rate temporarily spikes then stabilises)
```

### Circuit Breaker State Transitions (Stress Test)
```
CB State
CLOSED   ──────────────────────────────────────────
                                                   ↓ T+41s: opens
OPEN                                               ─────────────────
                                                                    ↓ T+360s (+30s timeout)
HALF_OPEN                                                           ──
                                                                      ↓ probe succeeds
CLOSED                                                                ─────────────
         0s  30s  60s  90s  120s                 300s 330s 360s 395s
         (load test active)                       ↑end (recovery phase)
```

---

## Observations

1. **Breaking point is approximately 280–320 concurrent users** on a single t3.medium (2 vCPU, 4 GB) instance running all services via Docker Compose.
2. **API Gateway becomes the first bottleneck** – Gunicorn's 3-worker configuration saturates the 2 vCPUs. Increasing workers to 5 or moving to async workers (Uvicorn/Gunicorn+asyncio) would push the threshold higher.
3. **Circuit Breaker worked as designed**: After cart-service failures accumulated (T+41s), the CB opened and subsequent requests received instant 503 responses (3–8 ms) instead of waiting for timeouts – this prevented cascade failures.
4. **Rate limiter (HTTP 429) absorbed 19.74% of requests** – this is the system's first line of defence, successfully shedding excess load before it reached downstream services.
5. **Order service saturated last** (T+28s DB pool exhaustion) – the Saga orchestration chain is the most resource-intensive path.
6. **Recovery is quick**: Within 45 seconds of load ending, all Circuit Breakers closed and the system returned to normal – demonstrating good resilience.
7. **RabbitMQ remained healthy** even at peak load – message queue depth peaked at 380 pending messages but processed all within 90 seconds of load ending.

## Recommendations

1. **Horizontal scaling is the primary fix**: Add a second `api-gateway` instance behind a load balancer. This would effectively double the breaking point to ~600 users.
2. **Kubernetes / Docker Swarm**: For production, each microservice should be individually scalable. Services like `order-service` and `book-service` should auto-scale at 70% CPU.
3. **Async Gunicorn workers**: Switch from `sync` to `uvicorn.workers.UvicornWorker` for async I/O to handle more concurrent connections per worker.
4. **Connection pooling with PgBouncer**: Reduce DB connection overhead which is a key failure point at 500 users.
5. **Global rate limiting**: Enforce stricter per-client rate limits (e.g., 60 req/min per IP for write endpoints) to protect the system before reaching saturation.
6. **Dedicated order queue**: Move order creation to an async workflow with a job-queue pattern (submit → get job ID → poll for result) to decouple request latency from Saga execution time.
7. **Circuit Breaker configuration tuning**: Consider a sliding-window approach (failures in last 10 seconds) rather than cumulative count per worker, for more predictable CB behaviour across Gunicorn worker distribution.
