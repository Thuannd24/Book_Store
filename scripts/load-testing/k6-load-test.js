/**
 * K6 Load Testing Script – BookStore Microservices
 * =================================================
 * Scenarios:
 *   - normalLoad:  50 VUs for 5 minutes  (smoke / normal)
 *   - peakLoad:   200 VUs for 10 minutes (peak)
 *   - stressTest: ramp to 500 VUs        (stress / breaking point)
 *
 * Usage:
 *   # Run all scenarios (defined below)
 *   k6 run scripts/load-testing/k6-load-test.js
 *
 *   # Run a single scenario by name
 *   k6 run --env SCENARIO=normalLoad scripts/load-testing/k6-load-test.js
 *
 *   # Override host
 *   k6 run --env BASE_URL=http://35.175.245.212:8080 scripts/load-testing/k6-load-test.js
 *
 * Install K6:
 *   # Ubuntu/Debian
 *   sudo gpg --no-default-keyring \
 *     --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
 *     --keyserver hkp://keyserver.ubuntu.com:80 \
 *     --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
 *   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] \
 *     https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
 *   sudo apt-get update && sudo apt-get install k6
 */

import http from "k6/http";
import { check, sleep, group } from "k6";
import { Rate, Trend, Counter } from "k6/metrics";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";

// Select a single scenario via env var, or run all
const SCENARIO_NAME = __ENV.SCENARIO || null;

// ---------------------------------------------------------------------------
// Custom metrics
// ---------------------------------------------------------------------------

const errorRate = new Rate("error_rate");
const orderLatency = new Trend("order_creation_latency");
const cartLatency = new Trend("cart_view_latency");
const bookLatency = new Trend("book_list_latency");
const cbOpenCount = new Counter("circuit_breaker_open_count"); // HTTP 503

// ---------------------------------------------------------------------------
// Scenario definitions
// ---------------------------------------------------------------------------

const allScenarios = {
  normalLoad: {
    executor: "ramping-vus",
    startVUs: 0,
    stages: [
      { duration: "30s", target: 10 },   // warm-up
      { duration: "30s", target: 50 },   // ramp to 50
      { duration: "4m",  target: 50 },   // steady state
      { duration: "30s", target: 0 },    // ramp down
    ],
    gracefulRampDown: "10s",
    tags: { scenario: "normalLoad" },
  },

  peakLoad: {
    executor: "ramping-vus",
    startVUs: 0,
    stages: [
      { duration: "1m",  target: 100 },  // ramp to 100
      { duration: "1m",  target: 200 },  // ramp to 200
      { duration: "8m",  target: 200 },  // steady state
      { duration: "1m",  target: 0 },    // ramp down
    ],
    gracefulRampDown: "30s",
    tags: { scenario: "peakLoad" },
  },

  stressTest: {
    executor: "ramping-vus",
    startVUs: 0,
    stages: [
      { duration: "1m",  target: 100 },  // warm-up
      { duration: "1m",  target: 300 },  // approaching limit
      { duration: "1m",  target: 500 },  // stress
      { duration: "3m",  target: 500 },  // sustain
      { duration: "1m",  target: 0 },    // ramp down
    ],
    gracefulRampDown: "30s",
    tags: { scenario: "stressTest" },
  },
};

// Apply scenario filter if set
export const options = {
  scenarios: SCENARIO_NAME
    ? { [SCENARIO_NAME]: allScenarios[SCENARIO_NAME] }
    : allScenarios,

  thresholds: {
    // Normal load thresholds
    "http_req_duration{scenario:normalLoad}":   ["p(95)<200", "p(99)<400"],
    // Peak load thresholds (relaxed)
    "http_req_duration{scenario:peakLoad}":     ["p(95)<500", "p(99)<1000"],
    // Stress test thresholds (just measure, no pass/fail)
    "http_req_duration{scenario:stressTest}":   ["p(99)<15000"],
    // Overall error rate: must be below 5% across all scenarios
    "error_rate":                               ["rate<0.05"],
    // CB-triggered 503s tracked separately (informational)
    "circuit_breaker_open_count":               [],
  },

  // Graceful stop after scenarios complete
  gracefulStop: "30s",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BOOK_IDS = Array.from({ length: 30 }, (_, i) => i + 1);
const CUSTOMER_IDS = Array.from({ length: 10 }, (_, i) => i + 1);

function randItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randFloat(min, max) {
  return Math.round((Math.random() * (max - min) + min) * 100) / 100;
}

// ---------------------------------------------------------------------------
// Main virtual user function
// ---------------------------------------------------------------------------

export default function () {
  const customerId = randItem(CUSTOMER_IDS);
  const bookId = randItem(BOOK_IDS);

  // ── Group 1: Health check (every VU, every iteration) ──
  group("health_check", () => {
    const res = http.get(`${BASE_URL}/api/health/`, {
      tags: { endpoint: "health" },
    });
    check(res, { "health: status 200": (r) => r.status === 200 });
    errorRate.add(res.status >= 500);
    if (res.status === 503) cbOpenCount.add(1);
  });

  sleep(0.5);

  // ── Group 2: Browse books (most common action) ──
  group("browse_books", () => {
    const listRes = http.get(`${BASE_URL}/api/gateway/books/api/books/`, {
      tags: { endpoint: "book_list" },
    });
    bookLatency.add(listRes.timings.duration);
    check(listRes, {
      "book list: ok": (r) => r.status === 200 || r.status === 429,
    });
    errorRate.add(listRes.status >= 500 && listRes.status !== 503);
    if (listRes.status === 503) cbOpenCount.add(1);

    sleep(0.3);

    const detailRes = http.get(
      `${BASE_URL}/api/gateway/books/api/books/${bookId}/`,
      { tags: { endpoint: "book_detail" } }
    );
    check(detailRes, {
      "book detail: ok": (r) =>
        r.status === 200 || r.status === 404 || r.status === 429,
    });
    errorRate.add(detailRes.status >= 500 && detailRes.status !== 503);
  });

  sleep(1);

  // ── Group 3: Cart operations ──
  group("cart_operations", () => {
    const cartRes = http.get(
      `${BASE_URL}/api/gateway/carts/api/carts/customer/${customerId}/`,
      { tags: { endpoint: "cart_view" } }
    );
    cartLatency.add(cartRes.timings.duration);
    check(cartRes, {
      "cart view: ok": (r) =>
        r.status === 200 || r.status === 404 || r.status === 429 || r.status === 503,
    });
    errorRate.add(cartRes.status >= 500 && cartRes.status !== 503);
    if (cartRes.status === 503) cbOpenCount.add(1);
  });

  sleep(1);

  // ── Group 4: Order creation (1-in-5 chance to simulate realistic ratio) ──
  if (Math.random() < 0.2) {
    group("create_order", () => {
      const payload = JSON.stringify({
        customer_id: customerId,
        items: [
          {
            book_id: bookId,
            quantity: Math.floor(Math.random() * 3) + 1,
            unit_price: randFloat(9.99, 49.99),
          },
        ],
        shipping_address: "123 Test Street, Ho Chi Minh City",
      });

      const orderRes = http.post(
        `${BASE_URL}/api/gateway/orders/api/orders/`,
        payload,
        {
          headers: { "Content-Type": "application/json" },
          tags: { endpoint: "order_create" },
          timeout: "30s",
        }
      );

      orderLatency.add(orderRes.timings.duration);
      check(orderRes, {
        "order: created or expected error": (r) =>
          [200, 201, 400, 422, 429, 503].includes(r.status),
      });
      errorRate.add(orderRes.status >= 500 && orderRes.status !== 503);
      if (orderRes.status === 503) cbOpenCount.add(1);
    });
  }

  sleep(Math.random() * 2 + 1); // 1–3 second think time
}

// ---------------------------------------------------------------------------
// Lifecycle hooks
// ---------------------------------------------------------------------------

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    metrics: {
      http_req_duration: data.metrics.http_req_duration,
      error_rate: data.metrics.error_rate,
      http_reqs: data.metrics.http_reqs,
      book_list_latency: data.metrics.book_list_latency,
      cart_view_latency: data.metrics.cart_view_latency,
      order_creation_latency: data.metrics.order_creation_latency,
      circuit_breaker_open_count: data.metrics.circuit_breaker_open_count,
    },
  };

  return {
    stdout: JSON.stringify(summary, null, 2),
    "docs/load-testing/results/k6-summary.json": JSON.stringify(summary, null, 2),
  };
}
