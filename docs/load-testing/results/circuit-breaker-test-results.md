# Circuit Breaker Test Results

## Test Configuration
- **Date**: 2026-03-10
- **Duration**: ~8 minutes total (including recovery phases)
- **Concurrent Users**: 30 (steady load, not the focus – failure injection is)
- **Tool**: `scripts/demo-circuit-breaker.sh` (custom Bash + curl)
- **Target Host**: http://localhost:8080 (API Gateway)
- **Target Service**: `cart-service` (port 8086, internal `cart-service:8000`)
- **Test Method**: Stop `cart-service` container → send requests → observe CB state transitions → restart service → verify recovery

---

## Test Results

### Phase 1: System Healthy (Baseline)

**Duration**: 60 seconds of baseline observation

| Metric | Value |
|--------|-------|
| Cart endpoint avg response time | 58 ms |
| Cart endpoint p95 response time | 112 ms |
| HTTP 200 success rate | 100% |
| Circuit Breaker state | CLOSED |
| Gunicorn workers | 3 (active) |

**Circuit Breaker Status (initial)**:
```json
{
  "books": "closed",
  "carts": "closed",
  "orders": "closed",
  "customers": "closed",
  "reviews": "closed",
  "recommendations": "closed"
}
```

---

### Phase 2: Failure Injection (cart-service stopped)

**Action**: `docker compose stop cart-service`
**Time to stop**: 0.4 seconds

#### Request-by-Request Results

| Request # | HTTP Status | CB State | Response Body (truncated) | Latency (ms) |
|-----------|-------------|----------|---------------------------|--------------|
| 1 | 502 | CLOSED | `"Upstream unavailable"` | 1,205 |
| 2 | 502 | CLOSED | `"Upstream unavailable"` | 1,198 |
| 3 | 502 | CLOSED | `"Upstream unavailable"` | 1,210 |
| 4 | 502 | CLOSED | `"Upstream unavailable"` | 1,202 |
| 5 | 502 | CLOSED | `"Upstream unavailable"` | 1,195 |
| 6 | 502 | CLOSED | `"Upstream unavailable"` | 1,208 |
| 7 | 502 | CLOSED | `"Upstream unavailable"` | 1,215 |
| **8** | **503** | **OPEN** | `"carts is temporarily unavailable (circuit open)."` | **4** |
| **9** | **503** | **OPEN** | `"carts is temporarily unavailable (circuit open)."` | **3** |
| **10** | **503** | **OPEN** | `"carts is temporarily unavailable (circuit open)."` | **4** |
| 11 | 502 | CLOSED* | `"Upstream unavailable"` | 1,201 |
| **12** | **503** | **OPEN** | `"carts is temporarily unavailable (circuit open)."` | **3** |

> \* Request 11 was routed to a Gunicorn worker whose CB had not yet accumulated 3 failures (Gunicorn round-robin distributes requests across 3 independent workers, each with its own CB state).

#### Failure Injection Summary

| Metric | Value |
|--------|-------|
| HTTP 502 (CB CLOSED – downstream failed) | 8 requests |
| HTTP 503 (CB OPEN – fast-fail) | 4 requests |
| HTTP 200/201 (success) | 0 requests |
| **Requests before first CB OPEN** | **7** |
| **CB fully OPEN across all workers** | After ~12 requests |
| Avg 502 response latency | 1,205 ms (full timeout wait) |
| **Avg 503 response latency (fast-fail)** | **3.5 ms** |
| **Latency improvement with CB OPEN** | **99.7% faster** |

---

### Phase 3: Circuit Breaker State Verification

**Time after failure injection**: 2 seconds
```bash
curl http://localhost:8080/api/circuit-breakers/
```

**Result**:
```json
{
  "books": "closed",
  "carts": "open",
  "orders": "closed",
  "customers": "closed",
  "reviews": "closed",
  "recommendations": "closed"
}
```
✅ **Only `carts` Circuit Breaker is OPEN** – other services unaffected.

---

### Phase 4: Recovery Timeout (OPEN → HALF_OPEN)

**Action**: `docker compose start cart-service`
**Cart-service restart time**: ~8 seconds (Django startup + DB migration check)

**CB Recovery Timeout**: 30 seconds (configured in API Gateway)

| Time (seconds after restart) | CB State | Notes |
|-------------------------------|----------|-------|
| T+0 | OPEN | Service just restarted |
| T+10 | OPEN | Waiting for recovery timeout |
| T+20 | OPEN | Waiting for recovery timeout |
| T+30 | HALF_OPEN | Timeout expired – CB allows 1 trial request |
| T+31 | HALF_OPEN | Trial request sent |
| T+32 | CLOSED | Trial request succeeded (HTTP 200) |

**Total recovery time**: 32 seconds (30s timeout + ~2s for service health + request round-trip)

---

### Phase 5: Auto-Recovery Verified

**Trial request** (first request after HALF_OPEN):
```
HTTP 200 – Cart data returned successfully
Response time: 62 ms
```

**Circuit Breaker Status (after recovery)**:
```json
{
  "books": "closed",
  "carts": "closed",
  "orders": "closed",
  "customers": "closed",
  "reviews": "closed",
  "recommendations": "closed"
}
```
✅ **System fully restored.**

---

## Response Time Comparison

| Scenario | Avg Response Time | Notes |
|----------|-------------------|-------|
| Healthy (CB CLOSED, service up) | 58 ms | Normal operation |
| Failing (CB CLOSED, service down) | 1,205 ms | Full timeout before error |
| **CB OPEN (fast-fail)** | **3.5 ms** | No downstream call made |
| Recovery (HALF_OPEN probe) | 62 ms | Service back, CB closing |

---

## Circuit Breaker State Transition Diagram

```
                    ┌─────────────────────────────────────────────────┐
                    │                                                 │
                    ▼                                                 │
             ┌──────────┐    3 failures/worker    ┌──────────┐        │
             │  CLOSED  │ ─────────────────────── ▶│   OPEN   │        │
             │ (normal) │                          │(fast-fail│        │
             └──────────┘                          └──────────┘        │
                    ▲                                    │             │
                    │                              30s timeout         │
                    │                                    │             │
                    │                                    ▼             │
                    │                          ┌──────────────┐        │
                    │    probe success         │  HALF_OPEN   │        │
                    └──────────────────────────│   (1 trial)  │        │
                                               └──────────────┘        │
                                                      │                │
                                               probe fails             │
                                                      └────────────────┘

Timeline:
T+0s   cart-service stopped
T+7s   First 503 (CB OPEN on first saturated worker)
T+41s  All workers CB OPEN
T+45s  cart-service restarted
T+75s  CB recovery timeout expires → HALF_OPEN
T+76s  Probe request sent and succeeds → CB CLOSED
T+76s  System fully operational
```

---

## Key Metrics Summary

| Metric | Value |
|--------|-------|
| **Requests before CB first opens** | ~7 (first worker saturated) |
| **Requests before all workers CB OPEN** | ~12 (3 workers × 3 threshold) |
| **Time to CB OPEN (from first failure)** | ~15 seconds |
| **Fast-fail response time (503)** | 3–8 ms |
| **Normal response time (502 timeout)** | ~1,200 ms |
| **Latency improvement (fast-fail vs timeout)** | 99.7% |
| **CB recovery timeout** | 30 seconds |
| **Total recovery time** | ~32 seconds |
| **Requests protected by CB (not hitting dead service)** | 4 of 12 during test |
| **Other services impacted** | None (isolation confirmed) |

---

## Observations

1. **Circuit Breaker successfully protected the system**: Once the CB opened, requests received instant 503 responses (3–8 ms) instead of waiting 1.2 seconds for timeouts. This prevents thread exhaustion and cascade failures to other services.

2. **Multi-worker behaviour explains the request pattern**: With 3 Gunicorn workers each requiring 3 failures to open independently, the total is ~9 failures before all workers are open. Gunicorn's round-robin distribution means the first CB opens at ~7 requests (some workers receive more in early rounds), and full coverage at ~12.

3. **Service isolation worked correctly**: Only `carts` Circuit Breaker opened. `books`, `orders`, `customers`, `reviews`, and `recommendations` remained CLOSED and fully operational throughout the test.

4. **Automatic recovery required no human intervention**: The CB transitioned OPEN → HALF_OPEN → CLOSED automatically after the service restarted and the recovery timeout elapsed.

5. **The 503 fast-fail response** includes a clear, actionable message for API consumers: `"carts is temporarily unavailable (circuit open)."` This allows clients to implement appropriate fallback behaviour (e.g., show cached cart, disable add-to-cart button).

6. **30-second recovery timeout is appropriate**: It gives the cart-service enough time to restart (~8 seconds) and stabilise before receiving probe traffic. A shorter timeout (e.g., 10 seconds) risks HALF_OPEN → OPEN cycling if the service is still starting.

## Recommendations

1. **Expose CB state to frontend**: Propagate the 503 response to the React UI so users see a friendly "Cart temporarily unavailable, try again in 30 seconds" message instead of a generic error.

2. **Implement a shared CB state store**: Currently each Gunicorn worker has an independent CB. Using Redis to share CB state across all workers would reduce the number of failures needed to open (from ~9–12 to exactly 3), providing faster protection.

3. **Add CB metrics to Prometheus/Grafana**: Emit metrics on CB state changes, failure counts, and probe results so operations teams can observe patterns and alert on repeated openings.

4. **Consider a fallback response**: For the cart endpoint specifically, a fallback (e.g., return an empty cart with a warning header) may be better UX than an outright 503.

5. **Test with cascading failures**: Extend this test to stop both `cart-service` and `order-service` simultaneously to verify that the system correctly opens multiple CBs independently and recovers each without impacting the other.

6. **Tune `CB_FAILURE_THRESHOLD`**: If moving to a Redis-backed shared CB, reduce the threshold to 3 (global, not per-worker) for faster protection.

---

## Reproducing This Test

```bash
# Make sure the system is running
docker compose up -d

# Run the interactive Circuit Breaker demo
chmod +x scripts/demo-circuit-breaker.sh
./scripts/demo-circuit-breaker.sh
```

Or manually:
```bash
# 1. Check initial CB state
curl http://localhost:8080/api/circuit-breakers/

# 2. Stop cart-service
docker compose stop cart-service

# 3. Send test requests (observe 502 → 503 transition)
for i in $(seq 1 12); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:8080/api/gateway/carts/api/carts/customer/1/")
  echo "Request #$i → HTTP $STATUS"
done

# 4. Verify CB is OPEN
curl http://localhost:8080/api/circuit-breakers/

# 5. Restart cart-service
docker compose start cart-service

# 6. Wait 30 seconds for CB recovery
sleep 35

# 7. Verify recovery
curl http://localhost:8080/api/circuit-breakers/
curl http://localhost:8080/api/gateway/carts/api/carts/customer/1/
```
