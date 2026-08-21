# Distributed-Order-Pipeline
# Distributed Order Pipeline (working title: OrderFlow)

**One-liner:** An event-driven, microservices-based order processing system demonstrating service decoupling, concurrency-safe inventory handling, and failure resilience — using an e-commerce order flow as the domain.

**Resume framing:** "Event-Driven Order Processing System (Microservices Architecture)" — not "e-commerce app." The commerce domain is context, the architecture is the point.

---

## 1. What this project actually demonstrates

- Service decomposition and independent deployability
- Event-driven communication (pub/sub) vs. direct service-to-service calls
- Concurrency-safe state management under race conditions
- Per-service data ownership (no shared database)
- Failure isolation, retries, and dead-letter handling
- Distributed tracing via correlation IDs
- Containerized orchestration (Docker Compose)

---

## 2. Services

### API Gateway
- Single entry point for all client requests
- Validates JWT on incoming requests, forwards to the right service
- Attaches a correlation ID (UUID) to every request, passed via header to downstream services
- Tech: Traefik, or a thin FastAPI reverse-proxy if you want it in Python

### Auth Service *(optional — see note below)*
- Issues JWTs on login/register
- Owns its own user table (id, email, hashed password, created_at)
- Endpoints: `POST /register`, `POST /login`, `GET /verify`

### Order Service (the orchestrator)
- Owns order records and order state machine: `pending → reserved → paid → confirmed → failed`
- Endpoints: `POST /orders` (place order), `GET /orders/{id}`, `GET /orders/{id}/status`
- On `POST /orders`:
  1. Synchronously calls Inventory Service to reserve stock
  2. If reserved, publishes `OrderCreated` event
  3. Consumes `PaymentSucceeded` / `PaymentFailed` events to update state
  4. On success, publishes `OrderConfirmed`
- Own DB: `orders` table (id, user_id, items JSON, status, total, timestamps)

### Inventory Service (the hard-logic centerpiece)
- Owns stock levels per product
- Endpoints: `POST /reserve`, `POST /release`, `POST /confirm`, `GET /stock/{product_id}`
- Reserve/release/confirm flow prevents overselling under concurrent requests
- Own DB: `products` table (id, name, stock_quantity, version — for optimistic locking) + `reservations` table (id, order_id, product_id, quantity, status, expires_at)
- **This is where you implement and test the race condition fix** — either `SELECT ... FOR UPDATE` row locking or optimistic concurrency with a version column

### Payment Service
- Consumes `OrderCreated` events
- Calls Stripe in test mode (or a mock if you want to avoid API key hassle)
- Publishes `PaymentSucceeded` or `PaymentFailed`
- Own DB: `payments` table (id, order_id, amount, status, stripe_ref, timestamps)

### Notification Service
- Consumes `OrderConfirmed` events only — never called directly by any other service
- Sends email via SendGrid/Mailgun free tier (or logs convincingly if you'd rather skip email setup)
- Own DB (optional): `notifications` table to log what was sent, for demo purposes

---

## 3. Message bus

- RabbitMQ (recommended over Redis Streams here — gives you exchanges, retry, and dead-letter queues out of the box, which you want for the resilience story)
- Exchanges/queues:
  - `order.created` → consumed by Payment Service
  - `payment.succeeded` / `payment.failed` → consumed by Order Service
  - `order.confirmed` → consumed by Notification Service
  - A dead-letter queue per queue, for messages that fail processing after N retries

---

## 4. Data ownership rule

**Each service has its own Postgres database (or at minimum its own schema).** No service ever queries another service's tables directly. This is the detail that proves "microservices" rather than "modular monolith" — a shared DB across services is the most common tell that a project isn't really decoupled.

---

## 5. Cross-cutting concerns (this is what makes it "real")

- **Correlation ID**: generated at the gateway, passed via header (`X-Correlation-ID`) through every service call and included in every log line and event payload. Lets you trace one order's full journey across all services in the logs.
- **Health checks**: `GET /health` on every service, checked by Docker Compose
- **Retry + dead-letter**: failed event processing retries with exponential backoff (2-3 attempts), then routes to a dead-letter queue instead of silently dropping
- **Idempotency**: consumers should handle receiving the same event twice without double-processing (e.g., check order status before acting)

---

## 6. Explicitly NOT included (scope control)

To keep this a 3-week project instead of a 3-month one:
- No product browsing/search UI
- No admin dashboard
- No reviews/ratings/recommendations
- No real frontend beyond a bare test page or Postman/Insomnia collection to trigger requests
- Auth Service can be simplified to a single hardcoded test JWT if you're tight on time — it's not the point of this project and shouldn't eat your week

---

## 7. Tech stack summary

| Concern | Choice |
|---|---|
| Services | FastAPI (Python) |
| Message bus | RabbitMQ |
| Databases | PostgreSQL (one instance, separate DB/schema per service) |
| Gateway | Traefik or thin FastAPI proxy |
| Orchestration | Docker Compose |
| Payments | Stripe test mode |
| Email | SendGrid or Mailgun free tier |
| Tracing | Correlation ID via headers + structured logging |

---

## 8. Repo structure

```
orderflow/
├── docker-compose.yml
├── README.md
├── gateway/
│   ├── Dockerfile
│   └── app/
├── order-service/
│   ├── Dockerfile
│   └── app/
├── inventory-service/
│   ├── Dockerfile
│   └── app/
├── payment-service/
│   ├── Dockerfile
│   └── app/
├── notification-service/
│   ├── Dockerfile
│   └── app/
└── shared/
    └── (shared event schemas / correlation ID middleware, if factored out)
```

---

## 9. Definition of done (the demo)

You should be able to:
1. Run `docker-compose up` and have everything come up healthy
2. Place an order via the gateway and watch it flow through all 4 services to "confirmed," with an email sent
3. Fire two concurrent orders for the last unit of a product and show only one succeeds
4. Kill the Notification Service mid-flow and show the order still completes (email just queues)
5. Kill the Payment Service and show messages land in a dead-letter queue after retries, instead of vanishing
6. Grep the logs by correlation ID and see one order's full path across all 4 services

Record a 2-3 minute video of points 2-5. That video is your strongest interview artifact.
