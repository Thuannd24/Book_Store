# Load Testing Scripts – BookStore Microservices

This directory contains load testing scripts for the BookStore Microservices system. Scripts cover normal, peak, and stress load scenarios using **Locust** (Python) and **K6** (JavaScript).

---

## Prerequisites

### 1. System must be running
```bash
cd /path/to/BookStorebook_Microservices
docker compose up -d
docker compose ps   # all services should show "Up"
```

### 2. Install Locust (Python)
```bash
pip install locust
# Verify:
locust --version
```

### 3. Install K6 (optional, for K6 scenarios)
```bash
# Ubuntu/Debian
sudo gpg --no-default-keyring \
  --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 \
  --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] \
  https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6

# macOS
brew install k6
```

---

## Files in This Directory

| File | Description |
|------|-------------|
| `locustfile.py` | Locust test script covering book browsing, cart, and order scenarios |
| `k6-load-test.js` | K6 test script with three named scenarios (normal / peak / stress) |
| `run-load-tests.sh` | Shell script to run all scenarios in sequence |
| `README.md` | This file |

---

## Quick Start

### Run all tests (automated)
```bash
chmod +x scripts/load-testing/run-load-tests.sh
./scripts/load-testing/run-load-tests.sh
```

### Run a specific scenario
```bash
# Normal load only (Locust)
./scripts/load-testing/run-load-tests.sh --scenario normal

# Peak load with K6
./scripts/load-testing/run-load-tests.sh --tool k6 --scenario peak

# Stress test against a remote server
./scripts/load-testing/run-load-tests.sh \
  --scenario stress \
  --host http://35.175.245.212:8080
```

---

## Locust – Usage

### Headless mode (CI / automated)
```bash
locust -f scripts/load-testing/locustfile.py \
  --host=http://localhost:8080 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --only-summary \
  --csv=docs/load-testing/results/normal-load
```

### Interactive web UI mode
```bash
locust -f scripts/load-testing/locustfile.py --host=http://localhost:8080
```
Then open **http://localhost:8089** in your browser.

### Scenario parameters

| Parameter | Normal Load | Peak Load | Stress Test |
|-----------|-------------|-----------|-------------|
| `--users` | 50 | 200 | 500 |
| `--spawn-rate` | 5 | 10 | 50 |
| `--run-time` | 5m | 10m | 5m |

### User classes in `locustfile.py`

| Class | Weight | Simulates |
|-------|--------|-----------|
| `BookBrowserUser` | 7 (70%) | Browsing books, checking health |
| `CartUser` | 2 (20%) | Viewing and updating shopping cart |
| `OrderUser` | 1 (10%) | Placing orders (Saga chain) |

---

## K6 – Usage

### Run a named scenario
```bash
# Normal load
k6 run --env SCENARIO=normalLoad scripts/load-testing/k6-load-test.js

# Peak load
k6 run --env SCENARIO=peakLoad scripts/load-testing/k6-load-test.js

# Stress test
k6 run --env SCENARIO=stressTest scripts/load-testing/k6-load-test.js

# All scenarios (default)
k6 run scripts/load-testing/k6-load-test.js
```

### Override target host
```bash
k6 run \
  --env BASE_URL=http://35.175.245.212:8080 \
  --env SCENARIO=normalLoad \
  scripts/load-testing/k6-load-test.js
```

### Export results to JSON
```bash
k6 run \
  --out json=docs/load-testing/results/k6-normal.json \
  --env SCENARIO=normalLoad \
  scripts/load-testing/k6-load-test.js
```

### K6 scenario definitions

| Scenario | VUs | Duration | Purpose |
|----------|-----|----------|---------|
| `normalLoad` | 50 | 5 min | Baseline performance |
| `peakLoad` | 200 | 10 min | Peak traffic simulation |
| `stressTest` | 500 | 5 min | Breaking point discovery |

---

## Circuit Breaker Test

The Circuit Breaker test uses the dedicated demo script:
```bash
chmod +x scripts/demo-circuit-breaker.sh
./scripts/demo-circuit-breaker.sh
```

This script:
1. Verifies all Circuit Breakers are CLOSED
2. Stops `cart-service` to inject failures
3. Sends 12 requests and observes CB state transitions (502 → 503)
4. Restarts `cart-service` and verifies automatic recovery

See [docs/load-testing/results/circuit-breaker-test-results.md](../../docs/load-testing/results/circuit-breaker-test-results.md) for detailed results.

---

## Interpreting Results

### Locust CSV output files
After a Locust run with `--csv=<prefix>`, you get:
- `<prefix>_stats.csv` – per-endpoint summary
- `<prefix>_stats_history.csv` – time series data
- `<prefix>_failures.csv` – failed requests details

### Key metrics to watch

| Metric | Normal Load Target | Peak Load Target |
|--------|--------------------|------------------|
| p95 response time | < 200 ms | < 500 ms |
| Error rate | < 1% | < 5% |
| HTTP 503 (CB open) | 0 | < 1% |
| CPU (api-gateway) | < 50% | < 90% |

### Monitoring during tests
```bash
# Real-time Docker stats
docker stats --format \
  "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Circuit Breaker state
watch -n 2 'curl -s http://localhost:8080/api/circuit-breakers/ | python3 -m json.tool'

# Service logs
docker compose logs -f api-gateway
```

---

## Results Documentation

Test result summaries are documented in:

| File | Scenario |
|------|----------|
| [`docs/load-testing/results/normal-load-results.md`](../../docs/load-testing/results/normal-load-results.md) | 50 users, 5 min |
| [`docs/load-testing/results/peak-load-results.md`](../../docs/load-testing/results/peak-load-results.md) | 200 users, 10 min |
| [`docs/load-testing/results/stress-test-results.md`](../../docs/load-testing/results/stress-test-results.md) | 500 users, 5 min |
| [`docs/load-testing/results/circuit-breaker-test-results.md`](../../docs/load-testing/results/circuit-breaker-test-results.md) | CB behaviour analysis |

---

## Troubleshooting

### "API Gateway not reachable"
```bash
docker compose up -d
docker compose ps
# Wait 60 seconds for all services to start
curl http://localhost:8080/api/health/
```

### "Locust not found"
```bash
pip install locust
# or with pip3
pip3 install locust
```

### "Permission denied on run-load-tests.sh"
```bash
chmod +x scripts/load-testing/run-load-tests.sh
```

### High error rate during normal load
- Check if rate limiting is configured too strictly (`RATE_LIMIT_ENABLED` in `.env`)
- Ensure all services are healthy: `docker compose ps`
- Review gateway logs: `docker compose logs api-gateway`

### Circuit Breakers not opening during stress test
- The CB threshold is 3 failures **per Gunicorn worker** (3 workers = ~9 total failures needed)
- Under load, workers share requests via round-robin – CB opens per-worker, not globally
- See [stress-test-results.md](../../docs/load-testing/results/stress-test-results.md) for detailed analysis
