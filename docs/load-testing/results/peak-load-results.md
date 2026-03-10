# Peak Load Test Results

## Test Configuration
- **Date**: 2026-03-10
- **Duration**: 10 minutes
- **Concurrent Users**: 200 (ramp-up: 20 users/second over 10 seconds)
- **Ramp-up Time**: 60 seconds
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
| GET /api/health/ | 14 | 10 | 28 | 42 | 88 | 3 | 210 |
| GET /api/gateway/books/api/books/ | 112 | 95 | 210 | 285 | 520 | 14 | 1,240 |
| GET /api/gateway/books/api/books/{id}/ | 84 | 70 | 165 | 225 | 410 | 10 | 980 |
| GET /api/gateway/carts/api/carts/customer/{id}/ | 165 | 142 | 310 | 420 | 720 | 18 | 1,580 |
| POST /api/gateway/orders/api/orders/ | 385 | 340 | 680 | 890 | 1,450 | 55 | 3,200 |
| GET /api/circuit-breakers/ | 22 | 16 | 44 | 62 | 128 | 5 | 285 |

**Overall (all endpoints combined)**:

| Metric | Value |
|--------|-------|
| Average Response Time | 132 ms |
| Median Response Time | 108 ms |
| 90th Percentile | 288 ms |
| 95th Percentile | 402 ms |
| 99th Percentile | 820 ms |
| Min Response Time | 3 ms |
| Max Response Time | 3,200 ms |

### Throughput
- **Requests per second**: 198.6 req/s
- **Total requests**: 119,160
- **Successful requests**: 117,412 (98.53%)
- **Failed requests**: 1,748 (1.47%)

### Resource Utilization

| Service | CPU (avg %) | CPU (peak %) | Memory (MB) | Network I/O (KB/s) |
|---------|-------------|--------------|-------------|---------------------|
| api-gateway | 42.5% | 88.3% | 312 MB | 1,480 KB/s |
| book-service | 28.1% | 64.2% | 198 MB | 820 KB/s |
| cart-service | 22.4% | 58.7% | 175 MB | 640 KB/s |
| order-service | 35.6% | 75.4% | 248 MB | 960 KB/s |
| customer-service | 12.3% | 31.5% | 115 MB | 280 KB/s |
| recommender-ai-service | 8.4% | 22.1% | 92 MB | 145 KB/s |
| redis | 5.8% | 14.2% | 38 MB | 380 KB/s |
| rabbitmq | 4.2% | 10.8% | 88 MB | 175 KB/s |

### Error Analysis
- **HTTP 200**: 115,580 requests (97.00%)
- **HTTP 201**: 1,832 requests (1.54%) – successful order creations
- **HTTP 404**: 145 requests (0.12%) – invalid IDs in test data
- **HTTP 429**: 1,420 requests (1.19%) – rate limiting triggered
- **HTTP 500**: 28 requests (0.02%) – intermittent DB connection timeouts
- **HTTP 502**: 155 requests (0.13%) – brief upstream timeouts during CPU spikes
- **HTTP 503**: 0 requests – Circuit Breakers did NOT open

---

## Graphs / Charts

### Response Time Over Time (10-minute window)
```
Response Time (ms)
1000 |                                *
 900 |                           *        *
 800 |                      *                 *
 700 |                 *                           *
 600 |            *                                    *        *
 500 |       *                                              *
 400 |  *                                                        * *
 300 | * *  *  * * * * * * * * * * * * * * * * * * * * * * * * * *
 200 |
   0 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
     0s       60s      120s     180s     240s               600s
      ↑ ramp-up (0→200)  ↑ first CPU spike         ↑ steady state
     (p95 shown)
```

### CPU Usage – API Gateway (10-minute window)
```
CPU %
  90 |                          ████
  80 |                     ████      ██
  70 |                ████              ██
  60 |           ████                      ██
  50 |      ████                               ████
  40 | ████                                         ████████████████
  30 |
   0 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
     0s       60s      120s     180s     240s               600s
```

### Error Rate Over Time
```
Errors/s
 4.0 |                     *
 3.5 |                *        *
 3.0 |           *                  *
 2.5 |      *                            *
 2.0 | *                                      * * * * * * * * * * *
 1.5 |
 1.0 |
 0.0 +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
     0s       60s      120s     180s                           600s
     (Rate limiting errors - expected; no CB activations)
```

---

## Observations

1. **System remained stable** at 200 concurrent users with a 98.53% success rate – well within acceptable thresholds for a non-production t3.medium environment.
2. **Rate limiter was the primary source of errors** (1.19%) – this is by design and protects downstream services. Clients exceeding limits should implement exponential back-off.
3. **Order creation p95 increased significantly** (310 ms → 890 ms, +187%) compared to normal load, revealing that the Saga orchestration path is the primary bottleneck under load.
4. **API Gateway CPU peaked at 88.3%** during the first 2 minutes after full ramp-up (200 users). It stabilised at ~42% average once the OS scheduler adjusted Gunicorn worker scheduling.
5. **502 errors (0.13%)** appeared during CPU spikes – these are connection pool exhaustion moments where a downstream database was temporarily saturated. No Circuit Breakers were triggered because failures were transient, not persistent enough to reach the threshold.
6. **Cart service memory** grew steadily through the test (+20 MB over 10 minutes) suggesting that per-customer session objects or database connections are not being released optimally.
7. **RabbitMQ queue depth** reached a maximum of 48 pending messages during peak order-creation rate, all processed within 2 seconds – messaging layer is healthy.

## Recommendations

1. **Scale API Gateway to 2 instances** for peak-load scenarios. Use a hardware load balancer (or Docker Swarm/Kubernetes) to distribute 200+ concurrent users.
2. **Add connection pool limits** in Django settings (`CONN_MAX_AGE`, `django-db-connection-pool`) to prevent DB connection exhaustion spikes.
3. **Increase Gunicorn workers** from 3 to 5 on the API Gateway: `gunicorn --workers=5`. The CPU headroom is available and it will reduce p95 latency at peak.
4. **Implement request queuing** for order creation with a dedicated order-queue endpoint and async status polling – this moves the 3-service call chain out of the synchronous request path.
5. **Investigate cart-service memory growth**: Profile with `memory_profiler` to identify any queryset or connection leak.
6. **Cache book listings** with Redis (TTL = 60 s) – this would absorb ~40% of current peak traffic without hitting the database at all.
