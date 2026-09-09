Bug: Inventory/Order services failing to create tables on startup

Symptom: On docker compose up, tables were never created in Postgres, even after multiple clean rebuilds (docker compose down -v followed by up). No errors were printed in the logs.

Investigation: Added a print(schema_sql) statement (with flush=True) right before executing the schema SQL, purely to confirm the SQL text was correct. Oddly, tables started appearing when this print statement was present, and disappeared again when it was removed — even across fully wiped, fresh runs.

Root cause: Docker Compose starts all services in parallel with no ordering guarantee by default. Postgres takes a few seconds to initialize and become ready to accept connections, while the lightweight Python services (inventory, order) start almost instantly and attempt to connect right away. The print statement was incidentally adding just enough delay to the Python service's startup path that Postgres was usually ready by the time the real connection attempt happened. Without it, the connection attempt consistently ran before Postgres had finished starting, since Postgres reliably took longer to start than the Python services did — a consistent ordering failure, not an intermittent race.

Fix: Added a healthcheck to the postgres service in docker-compose.yml using pg_isready, and added depends_on: condition: service_healthy to inventory, order, and payment services, so they explicitly wait for Postgres to report itself ready before starting, instead of relying on incidental timing.