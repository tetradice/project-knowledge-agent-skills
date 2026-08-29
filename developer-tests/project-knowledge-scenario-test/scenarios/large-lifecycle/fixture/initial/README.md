# Northstar Commerce Platform

Northstar is a fictional multi-tenant order platform used by stores in three regions. The repository contains a Python backend, TypeScript web console, operational tooling, and deployment definitions.

Requests enter through `gateway`; order state belongs to `orders`; stock reservations belong to `inventory`; delivery of email and webhook messages belongs to `notifications`. The web console never talks to internal services directly.

All public API requests require `X-Tenant-Id`. Mutating requests also require `Idempotency-Key`. PostgreSQL is the system of record. Redis is used only for short-lived cache entries and must not become an order authority.

See `docs/architecture/system-overview.md`, `docs/api/conventions.md`, and `docs/operations/deployment.md`. `docs/archive/v1-routing.md` is retained for historical context and is not current.
