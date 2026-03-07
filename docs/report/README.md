# Technical Report Outline (8–12 pages)
Use this as a scaffold; keep figures minimal and cite any external sources.

## Introduction
- Briefly describe the BookStore problem, target users (customers, staff, managers), and scope.

## Problem Statement
- What business needs are addressed (catalog, carts, orders, payments, shipping, reviews, recommendations).
- Non-goals (e.g., real payment gateway, fraud, large-scale throughput).

## Architecture
- Diagram of 12 services + Postgres-per-service.
- Rationale for microservices vs monolith and HTTP-based communication.

## Service Design
- One short paragraph per service: responsibility, main APIs, and key models.
- Note internal endpoints and why they are not exposed publicly.

## Implementation
- Tech stack (Django REST, Gunicorn, Postgres, docker-compose).
- Configuration via `DATABASE_URL`, env files, and per-service start scripts.
- Mention validation steps (book checks in cart, history in recommender).

## Docker/Deployment
- How images are built from service directories.
- Startup sequence (start.sh → makemigrations/migrate → gunicorn).
- Network assumptions (Docker internal DNS, ports listed in README).

## API Summary
- Table of critical endpoints (mirror `docs/api/README.md`).
- Expected request/response formats for 2–3 representative calls.

## Demo/Test Results
- Note manual demo steps and any automated tests run (`python manage.py test` per service).
- Observations on correctness and stability from running `docker-compose up --build`.

## Limitations
- Simplified auth (no JWT), synchronous calls, no retries, minimal validation.
- Single availability zone; no monitoring/metrics.

## Future Improvements
- Add auth tokens, circuit breakers/retries, async tasks for long-running work.
- Centralized logging/observability; CI for migrations/tests.
