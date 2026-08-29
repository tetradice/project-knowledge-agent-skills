# System overview

The gateway authenticates and normalizes public requests. Orders coordinates the business transaction but does not mutate stock directly. Inventory owns reservations and emits reservation outcomes. Notifications consumes committed events and never participates in the order transaction. The web console uses only gateway APIs.

PostgreSQL is authoritative. Redis entries are disposable. Events use an outbox in the same database transaction as aggregate changes. Consumers must be idempotent by event id.
