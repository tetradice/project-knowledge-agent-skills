# ADR 0002: Redis is disposable

Status: accepted

Redis stores short-lived read cache entries only. Order state, stock quantity, and reservation authority remain in PostgreSQL.
