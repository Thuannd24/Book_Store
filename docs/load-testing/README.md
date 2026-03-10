# Load Testing – BookStore Microservices

## Overview

This directory contains load testing documentation, results, and reproducible test scripts for the **BookStore Microservices** system. The goal is to validate performance, scalability, and resilience (including Circuit Breaker behaviour) under various traffic conditions.

---

## Test Environment

### Hardware (AWS EC2 – tested on)
| Resource | Specification |
|----------|---------------|
| Instance type | t3.medium |
| vCPUs | 2 |
| RAM | 4 GB |
| Network | Up to 5 Gbps |
| OS | Ubuntu 22.04 LTS |

### Docker Containers Resource Allocation
| Service | CPU Limit | Memory Limit | Replicas |
|---------|-----------|--------------|----------|
| api-gateway | 0.5 CPU | 512 MB | 1 |
| book-service | 0.5 CPU | 512 MB | 1 |
| cart-service | 0.5 CPU | 512 MB | 1 |
| order-service | 0.5 CPU | 512 MB | 1 |
| customer-service | 0.3 CPU | 256 MB | 1 |
| recommender-ai-service | 0.3 CPU | 256 MB | 1 |
| PostgreSQL (×12) | 0.2 CPU each | 256 MB each | 1 each |
| RabbitMQ | 0.2 CPU | 256 MB | 1 |
| Redis | 0.1 CPU | 128 MB | 1 |

> **Note**: Default `docker-compose.yml` does not set resource limits. The values above reflect recommended production-like limits added for load testing runs.

### API Gateway Configuration
- **Gunicorn workers**: 3
- **Circuit Breaker threshold**: 3 failures per worker → OPEN
- **Circuit Breaker recovery timeout**: 30 seconds
- **Rate limiting**: enabled (Redis-backed)

---

## Testing Tools

### Primary Tool – Locust (Python)
- **Version**: 2.x
- **Script**: [`/scripts/load-testing/locustfile.py`](../../scripts/load-testing/locustfile.py)
- **Why Locust**: Python-native, simple to extend, real-time web UI, compatible with the project's Django/Python stack.

### Secondary Tool – K6 (JavaScript)
- **Version**: 0.49+
- **Script**: [`/scripts/load-testing/k6-load-test.js`](../../scripts/load-testing/k6-load-test.js)
- **Why K6**: Low resource overhead, supports complex scenarios, excellent threshold assertions.

### Supplementary Tool – wrk
- Quick ad-hoc benchmarks during development.
- Example: `wrk -t4 -c50 -d30s http://localhost:8080/api/health/`

---

## Test Scenarios Summary

| Scenario | Concurrent Users | Duration | Key Metric |
|----------|-----------------|----------|------------|
| [Normal Load](results/normal-load-results.md) | 10–50 | 5 min | < 200 ms p95 |
| [Peak Load](results/peak-load-results.md) | 100–200 | 10 min | < 500 ms p95 |
| [Stress Test](results/stress-test-results.md) | 500+ | 5 min | Breaking point |
| [Circuit Breaker](results/circuit-breaker-test-results.md) | 30 | N/A | CB opens after ~9 failures |

---

## How to Reproduce Tests

### Prerequisites
```bash
# 1. Start the full stack
docker compose up -d

# 2. Wait for all services to be healthy (~60 seconds)
docker compose ps

# 3. Install Locust
pip install locust

# 4. Install K6 (optional)
# Ubuntu/Debian:
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6
```

### Run All Tests (Automated)
```bash
chmod +x scripts/load-testing/run-load-tests.sh
./scripts/load-testing/run-load-tests.sh
```

### Run Individual Scenarios
```bash
# Normal load (Locust headless)
locust -f scripts/load-testing/locustfile.py \
  --host=http://localhost:8080 \
  --users 50 --spawn-rate 5 \
  --run-time 5m --headless \
  --csv=docs/load-testing/results/normal-load

# Peak load
locust -f scripts/load-testing/locustfile.py \
  --host=http://localhost:8080 \
  --users 200 --spawn-rate 10 \
  --run-time 10m --headless \
  --csv=docs/load-testing/results/peak-load

# K6 stress test
k6 run --vus 500 --duration 5m scripts/load-testing/k6-load-test.js

# Circuit Breaker demo
./scripts/demo-circuit-breaker.sh
```

### Locust Web UI
```bash
locust -f scripts/load-testing/locustfile.py --host=http://localhost:8080
# Open http://localhost:8089 in your browser
```

---

## Key Findings Summary

| Finding | Detail |
|---------|--------|
| **Best performance** | `GET /api/gateway/books/api/books/` – avg 45 ms at 50 users |
| **Bottleneck** | Order creation (`POST /api/gateway/orders/api/orders/`) – involves 3 downstream service calls + RabbitMQ publish |
| **Circuit Breaker** | Opens after ~7–9 failed requests (3 workers × 3 threshold, distributed across round-robin) |
| **Breaking point** | System degrades significantly above 300 concurrent users on a t3.medium instance |
| **Recovery** | After cart-service restart, Circuit Breaker recovers within 30–35 seconds |

---

## Monitoring During Tests

### Live Docker Resource Usage
```bash
docker stats --no-stream --format \
  "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

### Circuit Breaker Status
```bash
curl -s http://localhost:8080/api/circuit-breakers/ | python3 -m json.tool
```

### Service Health Checks
```bash
for port in 8080 8083 8085 8086 8087; do
  echo -n "Port $port: "
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/api/health/
  echo
done
```

---

## References
- [`scripts/demo-circuit-breaker.sh`](../../scripts/demo-circuit-breaker.sh) – Interactive Circuit Breaker demo
- [`scripts/load-testing/locustfile.py`](../../scripts/load-testing/locustfile.py) – Locust scenarios
- [`scripts/load-testing/k6-load-test.js`](../../scripts/load-testing/k6-load-test.js) – K6 scenarios
- [`docs/architecture/README.md`](../architecture/README.md) – System architecture
- [`docs/fault-simulation.md`](../fault-simulation.md) – Fault injection guide
