#!/bin/bash
# Creates all OrderFlow project issues in your GitHub repo using the GitHub CLI.
#
# SETUP (one-time):
#   1. Install GitHub CLI: https://cli.github.com/
#   2. Run: gh auth login
#   3. cd into your repo (must already exist on GitHub, e.g. after `gh repo create`)
#   4. Run this script: bash create_github_issues.sh
#
# Optional: create milestones first in the GitHub UI (Week 1, Week 2, Week 3, Week 4)
# and uncomment the --milestone flags below to auto-assign issues to them.

set -e

# --- Labels (create once, safe to re-run) ---
gh label create "week-1" --color "0E8A16" --description "Foundation + inventory logic" --force
gh label create "week-2" --color "1D76DB" --description "Event chain" --force
gh label create "week-3" --color "5319E7" --description "Resilience + gateway" --force
gh label create "week-4" --color "D93F0B" --description "Polish + demo" --force
gh label create "core" --color "B60205" --description "Protect these if behind schedule" --force
gh label create "optional" --color "FBCA04" --description "Cut these first if behind schedule" --force

# --- Week 1 ---
gh issue create --title "Scaffold repo structure and Docker Compose skeleton" \
  --label "week-1" \
  --body "Create one folder per service (gateway, order, inventory, payment, notification), each a bare FastAPI app with a /health endpoint and its own Dockerfile. Write docker-compose.yml wiring all 5 services + Postgres + RabbitMQ together on one network.

**Done when:** \`docker-compose up\` starts everything and all /health endpoints respond."

gh issue create --title "Build Inventory Service with concurrency-safe reservations" \
  --label "week-1,core" \
  --body "Build products table (id, name, stock_quantity, version) and reservations table. Implement POST /reserve, POST /release, POST /confirm, GET /stock/{id}. Implement concurrency-safe reservation using row locking (SELECT ... FOR UPDATE) or optimistic concurrency with a version column.

**Done when:** a test firing two simultaneous requests for the last unit in stock reliably results in only one success, across 10+ repeated runs."

# --- Week 2 ---
gh issue create --title "Build Order Service and wire up RabbitMQ" \
  --label "week-2" \
  --body "Build orders table with state machine (pending -> reserved -> paid -> confirmed -> failed). POST /orders should call Inventory to reserve stock, then publish an OrderCreated event. Set up RabbitMQ exchanges/queues.

**Done when:** placing an order reserves stock and a message appears in the queue (no consumer needed yet)."

gh issue create --title "Build Payment Service as an event consumer" \
  --label "week-2" \
  --body "Payment Service consumes OrderCreated events, calls Stripe in test mode (or mocks it), and publishes PaymentSucceeded or PaymentFailed. Store payment records in its own DB.

**Done when:** an OrderCreated event results in a payment attempt and a result event being published."

gh issue create --title "Build Notification Service and complete the event chain" \
  --label "week-2,core" \
  --body "Order Service should consume PaymentSucceeded/PaymentFailed to update order status, and publish OrderConfirmed on success. Notification Service consumes OrderConfirmed and sends a confirmation email (SendGrid/Mailgun free tier, or log convincingly).

**Done when:** placing an order flows end-to-end to 'confirmed' and triggers an email. Screen-record this milestone."

# --- Week 3 ---
gh issue create --title "Add retry logic and dead-letter queues" \
  --label "week-3,core" \
  --body "Add retry with exponential backoff (2-3 attempts) on event consumers. Add dead-letter queues for messages that fail repeatedly.

**Done when:**
- Killing Notification Service mid-flow: order still completes, email sends once service recovers
- Killing Payment Service: messages queue instead of vanishing, then land in dead-letter queue after retries are exhausted"

gh issue create --title "Add API Gateway with correlation ID tracing" \
  --label "week-3,optional" \
  --body "Add Traefik (or a thin FastAPI proxy) in front of all services as a single entry point. Generate a correlation ID at the gateway, pass it via header through every downstream call, and log it in every service.

**Done when:** you can grep logs by a single correlation ID and see one order's full path across all 4 services."

gh issue create --title "(Optional) Build minimal frontend" \
  --label "week-3,optional" \
  --body "One page: product list, 'order now' button, order status view. Plain HTML/JS or React, functional not styled.

Skip entirely if behind schedule — a Postman/Insomnia collection is sufficient for the demo."

# --- Week 4 ---
gh issue create --title "Write README with architecture diagram" \
  --label "week-4" \
  --body "Document the architecture (simple boxes-and-arrows diagram is fine), docker-compose up quickstart instructions, and a 'chaos demo' section explaining what happens when a service dies."

gh issue create --title "Record demo video" \
  --label "week-4,core" \
  --body "Record a 2-3 minute video showing:
1. A normal order flowing through to confirmation + email
2. Two concurrent orders for the last unit in stock, only one succeeding
3. Killing a service mid-flow and the system surviving or recovering

This is your strongest interview artifact — link it or embed a GIF in the README."

gh issue create --title "Write resume bullets and finalize repo" \
  --label "week-4" \
  --body "Write resume bullets with architecture-first framing (e.g. 'Designed an event-driven order pipeline across 4 independently deployable services'), not 'e-commerce app' framing. Pin the repo on your GitHub profile. Add the demo video/GIF link to the top of the README."

echo ""
echo "All issues created. Run 'gh issue list' to review them."