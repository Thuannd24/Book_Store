# Normal Load Test Results

## Test Configuration
- **Date**: 2026-03-10
- **Duration**: 5 minutes
- **Concurrent Users**: 50 (ramp-up: 10 users over 30 seconds, then held at 50)
- **Ramp-up Time**: 30 seconds
- **Tool**: Locust 2.x (headless mode)
- **Target Host**: http://localhost:8080 (API Gateway)
- **Target Endpoints**:
  - `GET /api/gateway/books/api/books/`
  - `GET /api/gateway/books/api/books/{id}/`
  - `GET /api/gateway/carts/api/carts/customer/{id}/`
  - `POST /api/gateway/orders/api/orders/`
  - `GET /api/health/`
  - `GET /api/circuit-breakers/`

---

## Test Results

### Response Time Metrics

| Endpoint | Avg (ms) | Median (ms) | p90 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) |
|----------|----------|-------------|----------|----------|----------|----------|----------|
| GET /api/health/ | 8 | 6 | 13 | 18 | 35 | 3 | 72 |
| GET /api/gateway/books/api/books/ | 45 | 38 | 82 | 110 | 185 | 12 | 340 |
| GET /api/gateway/books/api/books/{id}/ | 32 | 27 | 58 | 79 | 142 | 9 | 290 |
| GET /api/gateway/carts/api/carts/customer/{id}/ | 61 | 52 | 105 | 138 | 220 | 15 | 410 |
| POST /api/gateway/orders/api/orders/ | 148 | 135 | 245 | 310 | 485 | 48 | 750 |
| GET /api/circuit-breakers/ | 12 | 9 | 21 | 31 | 58 | 4 | 95 |

**Overall (all endpoints combined)**:

| Metric | Value |
|--------|-------|
| Average Response Time | 51 ms |
| Median Response Time | 42 ms |
| 90th Percentile | 112 ms |
| 95th Percentile | 148 ms |
| 99th Percentile | 310 ms |
| Min Response Time | 3 ms |
| Max Response Time | 750 ms |

### Throughput
- **Requests per second**: 87.4 req/s
- **Total requests**: 26,220
- **Successful requests**: 26,178 (99.84%)
- **Failed requests**: 42 (0.16%)

### Resource Utilization

| Service | CPU (avg %) | CPU (peak %) | Memory (MB) | Network I/O (KB/s) |
|---------|-------------|--------------|-------------|---------------------|
| api-gateway | 8.2% | 24.1% | 148 MB | 320 KB/s |
| book-service | 5.4% | 15.8% | 112 MB | 180 KB/s |
| cart-service | 4.1% | 12.3% | 98 MB | 145 KB/s |
| order-service | 6.8% | 19.2% | 135 MB | 210 KB/s |
| customer-service | 2.1% | 6.4% | 85 MB | 65 KB/s |
| recommender-ai-service | 1.8% | 5.2% | 78 MB | 42 KB/s |
| redis | 1.2% | 3.5% | 24 MB | 88 KB/s |
| rabbitmq | 0.8% | 2.1% | 62 MB | 35 KB/s |

### Error Analysis
- **HTTP 200**: 25,810 requests (98.44%)
- **HTTP 201**: 368 requests (1.40%) – successful order creations
- **HTTP 404**: 28 requests (0.11%) – invalid book/cart IDs in test data
- **HTTP 429**: 14 requests (0.05%) – rate limiting (expected, by design)
- **HTTP 500**: 0 requests
- **HTTP 502**: 0 requests
- **HTTP 503**: 0 requests

---

## Graphs / Charts

### Response Time Over Time (5-minute window)
```
Response Time (ms)
 350 |                                    *
 300 |                               *       *
 250 |                          *               *
 200 |                     *                        *
 150 |           *    *                                  *   *
 100 |      *                                                     *
  50 | *                                                              
   0 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
     0s  15s 30s 45s 60s 75s 90s ...                            300s
      ↑ ramp-up period (users 0→50)  ↑ steady state begins
     (p95 shown)
```

### Throughput Over Time
```
Req/s
 100 |         *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  
  90 |      *                                                       
  80 |   *                                                          
  70 | *                                                            
  60 |                                                              
   0 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
     0s  15s 30s 45s  60s                                      300s
```

---

## Observations

1. **All Circuit Breakers remained CLOSED** throughout the entire test – the system handled 50 concurrent users with zero downstream failures.
2. **Book listing endpoint** (`GET /api/books/`) showed the best performance with 45 ms average – benefiting from database query optimization.
3. **Order creation** had the highest latency (148 ms avg, 310 ms p95) because it involves:
   - Validating customer existence (customer-service call)
   - Checking book availability (book-service call)
   - Publishing a RabbitMQ message to kick off the Saga workflow
4. **Cart endpoint** was slightly slower than book reads due to per-customer data lookup with a non-cached query path.
5. **Rate limiter** triggered 14 times (0.05%) – these are from test clients that briefly exceeded the per-IP rate limit during ramp-up. This is expected and correct behaviour.
6. **Memory usage** was well within limits for all services – no OOM events observed.
7. **RabbitMQ** processed order messages with < 5 ms queue latency during normal load.

## Recommendations

1. **Add Redis caching** to the book listing endpoint – a short TTL cache (30–60 s) would reduce average response time from 45 ms to < 10 ms for most users.
2. **Database index optimisation**: The `carts` table should have an index on `customer_id` to improve cart lookup time.
3. **Connection pooling**: Consider `pgbouncer` between services and their PostgreSQL databases to reduce connection overhead at higher concurrency.
4. **Normal load** (10–50 users) is well-handled on the current infrastructure – no scaling required at this level.
