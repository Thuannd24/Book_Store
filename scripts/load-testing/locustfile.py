"""
Locust load testing script for BookStore Microservices
======================================================
Covers the three main API flows:
  1. Book browsing (read-heavy)
  2. Cart management (read + write)
  3. Order creation (write-heavy, multi-service Saga)

Usage:
  # Headless (CI / automated)
  locust -f locustfile.py --host=http://localhost:8080 \
    --users 50 --spawn-rate 5 --run-time 5m --headless

  # Web UI (interactive)
  locust -f locustfile.py --host=http://localhost:8080
  # Then open http://localhost:8089

Install:
  pip install locust
"""

import random
import json
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# ---------------------------------------------------------------------------
# Realistic sample data – mirrors scripts/book-data.json & customer-data.json
# ---------------------------------------------------------------------------
BOOK_IDS = list(range(1, 31))          # Books 1–30 assumed seeded
CUSTOMER_IDS = list(range(1, 11))      # Customers 1–10 assumed seeded
CATALOG_IDS = list(range(1, 6))        # Catalog categories 1–5


# ---------------------------------------------------------------------------
# User classes
# ---------------------------------------------------------------------------

class BookBrowserUser(HttpUser):
    """
    Simulates a user browsing the book catalogue.
    Weighted towards read operations – representative of 70% of real traffic.
    """
    weight = 7
    wait_time = between(1, 3)

    @task(5)
    def list_books(self):
        """Browse the full book listing (most common action)."""
        with self.client.get(
            "/api/gateway/books/api/books/",
            name="GET /books/",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            elif resp.status_code == 429:
                resp.success()  # Rate-limited – expected, not a failure
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(3)
    def get_book_detail(self):
        """Fetch details for a specific book."""
        book_id = random.choice(BOOK_IDS)
        with self.client.get(
            f"/api/gateway/books/api/books/{book_id}/",
            name="GET /books/{id}/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            elif resp.status_code == 429:
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(1)
    def check_health(self):
        """Health check – low weight, just to monitor gateway liveness."""
        self.client.get("/api/health/", name="GET /health/")

    @task(1)
    def check_circuit_breakers(self):
        """Monitor circuit breaker state – ops-style polling."""
        self.client.get("/api/circuit-breakers/", name="GET /circuit-breakers/")


class CartUser(HttpUser):
    """
    Simulates a logged-in customer managing their shopping cart.
    Mix of reads and writes – representative of 20% of real traffic.
    """
    weight = 2
    wait_time = between(2, 5)

    def on_start(self):
        """Each simulated user picks a random customer ID."""
        self.customer_id = random.choice(CUSTOMER_IDS)

    @task(3)
    def view_cart(self):
        """View the cart for the current customer."""
        with self.client.get(
            f"/api/gateway/carts/api/carts/customer/{self.customer_id}/",
            name="GET /carts/customer/{id}/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            elif resp.status_code in (429, 503):
                resp.success()  # CB or rate-limit – expected during stress
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(1)
    def add_to_cart(self):
        """Add a random book to the customer's cart."""
        book_id = random.choice(BOOK_IDS)
        payload = {
            "book_id": book_id,
            "quantity": random.randint(1, 3),
        }
        with self.client.post(
            f"/api/gateway/carts/api/carts/customer/{self.customer_id}/items/",
            json=payload,
            name="POST /carts/customer/{id}/items/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 400, 404):
                resp.success()
            elif resp.status_code in (429, 503):
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")


class OrderUser(HttpUser):
    """
    Simulates a customer placing an order.
    Write-heavy, exercises the Saga orchestration chain.
    Weighted at 10% of traffic – orders are less frequent than browsing.
    """
    weight = 1
    wait_time = between(5, 15)

    def on_start(self):
        self.customer_id = random.choice(CUSTOMER_IDS)

    @task(1)
    def create_order(self):
        """Place a new order (triggers Saga: book check → payment → shipment)."""
        book_id = random.choice(BOOK_IDS)
        payload = {
            "customer_id": self.customer_id,
            "items": [
                {
                    "book_id": book_id,
                    "quantity": 1,
                    "unit_price": round(random.uniform(9.99, 49.99), 2),
                }
            ],
            "shipping_address": "123 Test Street, Ho Chi Minh City",
        }
        with self.client.post(
            "/api/gateway/orders/api/orders/",
            json=payload,
            name="POST /orders/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 400, 422):
                resp.success()
            elif resp.status_code in (429, 503):
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(2)
    def list_orders(self):
        """Fetch order history for the current customer."""
        with self.client.get(
            f"/api/gateway/orders/api/orders/customer/{self.customer_id}/",
            name="GET /orders/customer/{id}/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            elif resp.status_code in (429, 503):
                resp.success()
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")


# ---------------------------------------------------------------------------
# Event hooks – print summary header when test starts
# ---------------------------------------------------------------------------

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    if not isinstance(environment.runner, MasterRunner):
        print("\n" + "=" * 60)
        print("  BookStore Microservices Load Test – Starting")
        print("  Target: http://localhost:8080")
        print("  Users:  BookBrowserUser (70%), CartUser (20%), OrderUser (10%)")
        print("=" * 60 + "\n")
