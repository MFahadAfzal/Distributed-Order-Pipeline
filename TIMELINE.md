# OrderFlow — Build Roadmap

Assumes part-time work (evenings/weekends). Total: ~4 weeks. Adjust up or down based on your actual hours.

---

## Week 1 — Foundation + hardest logic

**Days 1-2: Scaffold**
- Create repo structure: one folder per service (gateway, order, inventory, payment, notification)
- Each service: bare FastAPI app with a `/health` endpoint, its own Dockerfile
- Write `docker-compose.yml` with all 5 services + Postgres + RabbitMQ networked together
- ✅ Checkpoint: `docker-compose up` starts everything, all `/health` endpoints respond

**Days 3-5: Inventory Service (do this first — it's your hardest logic)**
- Build `products` table (id, name, stock_quantity, version) and `reservations` table
- Implement `POST /reserve`, `POST /release`, `POST /confirm`, `GET /stock/{id}`
- Implement concurrency-safe reservation (row locking or optimistic concurrency)
- Write a test that fires two simultaneous requests for the last unit in stock, assert only one wins
- ✅ Checkpoint: concurrency test passes reliably, re-run it 10 times to be sure

---

## Week 2 — The event chain

**Days 6-8: Order Service + RabbitMQ wiring**
- Build `orders` table and state machine (pending → reserved → paid → confirmed → failed)
- `POST /orders`: calls Inventory to reserve, then publishes `OrderCreated` event
- Set up RabbitMQ exchanges/queues
- ✅ Checkpoint: placing an order reserves stock and a message appears in the queue (nothing consumes it yet — that's fine)

**Days 9-11: Payment Service + Notification Service**
- Payment Service consumes `OrderCreated`, fakes/calls Stripe test mode, publishes `PaymentSucceeded`/`PaymentFailed`
- Order Service consumes that, updates status, publishes `OrderConfirmed` on success
- Notification Service consumes `OrderConfirmed`, sends email (SendGrid/Mailgun free tier or logs it)
- ✅ Checkpoint: full chain works end-to-end — place an order, watch it become "confirmed," get an email. **Screen-record this now, even rough.**

---

## Week 3 — The parts that make it "real"

**Days 12-14: Failure handling**
- Add retry with exponential backoff on event consumers (2-3 attempts)
- Add dead-letter queues for messages that fail repeatedly
- Test: kill Notification Service mid-flow → confirm order still completes
- Test: kill Payment Service → confirm messages queue instead of vanishing, then land in dead-letter after retries
- ✅ Checkpoint: both chaos tests behave correctly and you can explain why

**Days 15-16: Gateway + correlation IDs**
- Add Traefik (or thin FastAPI proxy) in front of all services
- Generate a correlation ID at the gateway, pass via header, log it in every service
- ✅ Checkpoint: you can grep logs by one correlation ID and see a single order's path across all 4 services

**Day 17 (optional): Minimal frontend**
- One page: product list, "order now" button, order status view
- Plain HTML/JS or React — functional, not styled
- Skip this entirely if you're behind schedule; a Postman collection works fine for the demo

---

## Week 4 — Polish and package

**Days 18-19: Documentation**
- README with a simple architecture diagram (boxes and arrows is fine)
- `docker-compose up` quickstart instructions
- Short "chaos demo" section explaining what happens when a service dies

**Day 20: Record the demo video (2-3 min)**
- Place a normal order, show it flow through to confirmation + email
- Fire two concurrent orders for the last unit, show only one succeeds
- Kill a service mid-flow, show the system survives or recovers
- This video matters more than people expect — it's proof you understand what you built, not just that it runs

**Day 21: Resume + repo cleanup**
- Write the resume bullets (architecture-first framing, not "e-commerce app")
- Pin the repo, add the video link or GIF to the README

---

## If you fall behind, cut in this order (last to first = most protected):
1. ~~Minimal frontend~~ — cut first, least impact on the story
2. ~~Gateway~~ — nice to have, not core to the architecture claim
3. ~~Auth~~ — hardcode a test token if you haven't built it yet
4. Correlation IDs — try to keep, cheap to add and interviewers like it
5. **Dead-letter/retry handling — protect this**
6. **Inventory concurrency handling — protect this above all**

The last two are your actual differentiators. Everything else is supporting cast.
