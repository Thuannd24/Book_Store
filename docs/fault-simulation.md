# Fault Simulation Guide – BookStore Microservices

This document describes how to simulate partial failures in the order creation saga and verify that compensation logic works correctly.

---

## Prerequisites

Start the full stack:

```bash
docker compose up -d
```

Wait until all services are healthy:

```bash
docker compose ps
```

---

## Saga Steps Recap

```
POST /api/gateway/orders/orders/
  → order-service: CREATE_ORDER (status: PENDING)
  → pay-service:   RESERVE_PAYMENT  (POST /internal/payments/)
  → ship-service:  RESERVE_SHIPPING (POST /internal/shipments/)
  → order-service: CONFIRM_ORDER (status: CONFIRMED)
```

---

## Scenario 1: pay-service Failure (RESERVE_PAYMENT fails)

### Steps

1. Stop the pay-service:
   ```bash
   docker compose stop pay-service
   ```

2. Trigger an order creation:
   ```bash
   curl -s -X POST http://localhost:8080/api/gateway/orders/orders/ \
     -H "Content-Type: application/json" \
     -d '{
       "customer_id": 1,
       "payment_method": "COD",
       "shipping_method": "STANDARD",
       "shipping_address": "123 Test St",
       "shipping_fee": "5.00"
     }' | python3 -m json.tool
   ```

3. **Expected result**: HTTP 502 with `{"detail": "Payment reservation failed."}` and order status `FAILED`.

4. Restart pay-service:
   ```bash
   docker compose start pay-service
   ```

---

## Scenario 2: ship-service Failure Mid-Saga (RESERVE_SHIPPING fails after payment reserved)

### Steps

1. Stop the ship-service:
   ```bash
   docker compose stop ship-service
   ```

2. Trigger an order creation (same as above).

3. **Expected result**:
   - HTTP 502 with `{"detail": "Shipment reservation failed; payment cancelled."}`.
   - Order status: `COMPENSATED`.
   - Payment status: `CANCELLED` (pay-service received DELETE call).
   - `saga_logs` table has `RESERVE_SHIPPING` step with status `FAILED` and `RESERVE_PAYMENT` with status `COMPENSATED`.

4. Verify saga log:
   ```bash
   docker compose exec order-service python manage.py shell -c "
   from orders.models import SagaLog
   for log in SagaLog.objects.order_by('-created_at')[:10]:
       print(log.order_id, log.step, log.status)
   "
   ```

5. Restart ship-service:
   ```bash
   docker compose start ship-service
   ```

---

## Scenario 3: Verify Normal Flow

1. Ensure all services are running.
2. Create an order.
3. **Expected result**: HTTP 201, order status `CONFIRMED`.
4. Check RabbitMQ management UI at `http://localhost:15672` (user: `bookstore`, pass: `bookstore123`) for `order.confirmed` event on the `orders` exchange.

---

## Using the RabbitMQ Management UI

1. Navigate to `http://localhost:15672`.
2. Login with `bookstore` / `bookstore123`.
3. Go to **Exchanges** → `orders` to see message rates.
4. Go to **Queues** to see any bound consumer queues.
5. Use **Get messages** to inspect event payloads.

---

## Inspecting SagaLog Table Directly

```bash
docker compose exec order-db psql -U postgres -d order_db -c \
  "SELECT order_id, step, status, created_at FROM saga_logs ORDER BY created_at DESC LIMIT 20;"
```

---

## Expected Saga Log Entries for a Successful Order

| order_id | step | status |
|---|---|---|
| 1 | CREATE_ORDER | COMPLETED |
| 1 | RESERVE_PAYMENT | STARTED |
| 1 | RESERVE_PAYMENT | COMPLETED |
| 1 | RESERVE_SHIPPING | STARTED |
| 1 | RESERVE_SHIPPING | COMPLETED |
| 1 | CONFIRM_ORDER | STARTED |
| 1 | CONFIRM_ORDER | COMPLETED |

## Expected Saga Log Entries When Shipping Fails (Compensation)

| order_id | step | status |
|---|---|---|
| 1 | CREATE_ORDER | COMPLETED |
| 1 | RESERVE_PAYMENT | STARTED |
| 1 | RESERVE_PAYMENT | COMPLETED |
| 1 | RESERVE_SHIPPING | STARTED |
| 1 | RESERVE_SHIPPING | FAILED |
| 1 | RESERVE_PAYMENT | COMPENSATED |

---

## Scenario 4: Circuit Breaker Tripping

### Trigger
Send 3 requests to create an order while `pay-service` is stopped:
```bash
docker compose stop pay-service
for i in 1 2 3 4; do
  curl -s -X POST http://localhost:8080/api/gateway/orders/orders/ \
    -H "Content-Type: application/json" \
    -d '{"customer_id":1,"payment_method":"COD","shipping_method":"STANDARD","shipping_address":"123 St","shipping_fee":"5.00"}' \
    | python3 -m json.tool
done
```

### Expected behaviour
- Requests 1–3: HTTP 502 (circuit attempts the call, failure is counted).
- Request 4+: HTTP 503 with `"pay-service circuit open"` (circuit is now OPEN, call rejected instantly).
- After 30 seconds: circuit transitions to HALF_OPEN and the next call is a probe.

### Check circuit state
```bash
curl http://localhost:8080/api/circuit-breakers/
```
Expected response:
```json
{"customers": "CLOSED", "books": "CLOSED", "orders": "OPEN", "carts": "CLOSED", "reviews": "CLOSED", "recommendations": "CLOSED", "catalog": "CLOSED", "staff": "CLOSED", "managers": "CLOSED"}
```
