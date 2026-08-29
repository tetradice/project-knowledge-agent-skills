# API conventions

Public routes are versioned under `/v1`. Every request requires `X-Tenant-Id`; POST, PUT, PATCH, and DELETE also require `Idempotency-Key`. Errors use `code`, `message`, and `trace_id`. Internal exception names and stack traces are never returned.

Dates are RFC 3339 UTC. Money is an integer minor-unit amount with a separate ISO currency code.
